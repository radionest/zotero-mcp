"""
Response chunking system for handling large responses that exceed token limits.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from .token_estimator import estimate_tokens


class ResponseChunker:
    """
    Handles response chunking for large Zotero results to stay within token limits.
    """
    
    def __init__(self, max_tokens: int = 20000):
        """
        Initialize the response chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (default: 20000 for safety margin)
        """
        self.max_tokens = max_tokens
        self.chunks_storage: Dict[str, List[str]] = {}
        self.storage_expiry: Dict[str, float] = {}
        self.ttl_seconds = 900  # 15 minutes
    
    def should_chunk(self, response: str) -> bool:
        """
        Determine if response needs chunking based on token count.
        
        Args:
            response: The response text to check
            
        Returns:
            True if response should be chunked, False otherwise
        """
        token_count = estimate_tokens(response)
        return token_count > self.max_tokens
    
    def chunk_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chunk a response into smaller pieces that fit within token limits.
        
        Args:
            response: The response text to chunk
            context: Optional context about the response type
            
        Returns:
            Dictionary with chunk information and continuation token
        """
        if not self.should_chunk(response):
            return {
                "chunked": False,
                "content": response,
                "total_tokens": estimate_tokens(response)
            }
        
        # Determine chunking strategy based on content
        if "## " in response:
            # Markdown with headers - chunk by items
            chunks = self._chunk_by_items(response)
        elif "\n\n" in response:
            # Paragraph-based chunking
            chunks = self._chunk_by_paragraphs(response)
        else:
            # Line-based chunking as fallback
            chunks = self._chunk_by_lines(response)
        
        # Store chunks and create continuation token
        chunk_id = str(uuid.uuid4())
        self.chunks_storage[chunk_id] = chunks
        self.storage_expiry[chunk_id] = time.time() + self.ttl_seconds
        
        # Clean up expired chunks
        self._cleanup_expired()
        
        return {
            "chunked": True,
            "chunk_id": chunk_id,
            "total_chunks": len(chunks),
            "current_chunk": 0,
            "content": chunks[0] if chunks else "",
            "continuation_token": f"{chunk_id}:1" if len(chunks) > 1 else None,
            "total_tokens": sum(estimate_tokens(chunk) for chunk in chunks)
        }
    
    def get_next_chunk(self, continuation_token: str) -> Dict[str, Any]:
        """
        Get the next chunk using a continuation token.
        
        Args:
            continuation_token: Token in format "chunk_id:chunk_index"
            
        Returns:
            Dictionary with next chunk information
        """
        try:
            chunk_id, chunk_index_str = continuation_token.split(":", 1)
            chunk_index = int(chunk_index_str)
        except (ValueError, AttributeError):
            return {"error": "Invalid continuation token"}
        
        # Check if chunks still exist and haven't expired
        if chunk_id not in self.chunks_storage:
            return {"error": "Chunks expired or not found"}
        
        if time.time() > self.storage_expiry.get(chunk_id, 0):
            self._cleanup_chunk(chunk_id)
            return {"error": "Chunks expired"}
        
        chunks = self.chunks_storage[chunk_id]
        
        if chunk_index >= len(chunks):
            return {"error": "Chunk index out of range"}
        
        # Prepare response
        next_continuation = None
        if chunk_index + 1 < len(chunks):
            next_continuation = f"{chunk_id}:{chunk_index + 1}"
        
        return {
            "chunked": True,
            "chunk_id": chunk_id,
            "total_chunks": len(chunks),
            "current_chunk": chunk_index,
            "content": chunks[chunk_index],
            "continuation_token": next_continuation
        }
    
    def _chunk_by_items(self, response: str) -> List[str]:
        """
        Chunk response by markdown items (sections starting with ##).
        """
        lines = response.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Keep the header
        header_lines = []
        for line in lines:
            if line.startswith('#') and not line.startswith('##'):
                header_lines.append(line)
            else:
                break
        
        header = '\n'.join(header_lines)
        header_tokens = estimate_tokens(header)
        
        # Process remaining lines
        item_start_idx = len(header_lines)
        current_chunk = header_lines.copy()
        current_tokens = header_tokens
        
        for line in lines[item_start_idx:]:
            if line.startswith('## ') and current_chunk and current_tokens > 0:
                # New item - check if we should start a new chunk
                line_tokens = estimate_tokens(line)
                
                if current_tokens + line_tokens > self.max_tokens:
                    # Save current chunk
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(chunk_text)
                    
                    # Start new chunk with header
                    current_chunk = header_lines.copy() + [line]
                    current_tokens = header_tokens + line_tokens
                else:
                    current_chunk.append(line)
                    current_tokens += line_tokens
            else:
                line_tokens = estimate_tokens(line)
                if current_tokens + line_tokens > self.max_tokens:
                    # Save current chunk
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(chunk_text)
                    
                    # Start new chunk with header
                    current_chunk = header_lines.copy() + [line]
                    current_tokens = header_tokens + line_tokens
                else:
                    current_chunk.append(line)
                    current_tokens += line_tokens
        
        # Add remaining content
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks or [response]
    
    def _chunk_by_paragraphs(self, response: str) -> List[str]:
        """
        Chunk response by paragraphs (double newlines).
        """
        paragraphs = response.split('\n\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = estimate_tokens(para)
            
            if current_tokens + para_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Add remaining content
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks or [response]
    
    def _chunk_by_lines(self, response: str) -> List[str]:
        """
        Fallback chunking by lines.
        """
        lines = response.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = estimate_tokens(line)
            
            if current_tokens + line_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        # Add remaining content
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks or [response]
    
    def _cleanup_expired(self):
        """Clean up expired chunks."""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.storage_expiry.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            self._cleanup_chunk(key)
    
    def _cleanup_chunk(self, chunk_id: str):
        """Clean up a specific chunk."""
        self.chunks_storage.pop(chunk_id, None)
        self.storage_expiry.pop(chunk_id, None)


# Global instance
_response_chunker = None

def get_response_chunker() -> ResponseChunker:
    """Get or create the global response chunker instance."""
    global _response_chunker
    if _response_chunker is None:
        _response_chunker = ResponseChunker()
    return _response_chunker