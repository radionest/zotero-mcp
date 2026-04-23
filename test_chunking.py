#!/usr/bin/env python3
"""
Test script to verify response chunking functionality.
"""

from src.zotero_mcp.response_chunker import ResponseChunker
from src.zotero_mcp.token_estimator import estimate_tokens

def test_token_estimation():
    """Test token estimation."""
    print("Testing token estimation...")
    
    # Test basic text
    text1 = "Hello world"
    tokens1 = estimate_tokens(text1)
    print(f"Text: '{text1}' -> Estimated tokens: {tokens1}")
    
    # Test longer text
    text2 = "A" * 100000  # 100k characters
    tokens2 = estimate_tokens(text2)
    print(f"100k character text -> Estimated tokens: {tokens2}")
    
    # Test markdown text
    text3 = "# Header\n**Bold** text with `code`"
    tokens3 = estimate_tokens(text3)
    print(f"Markdown text -> Estimated tokens: {tokens3}")
    
    print()

def test_chunking():
    """Test response chunking."""
    print("Testing response chunking...")
    
    # Create chunker with lower limit for testing
    chunker = ResponseChunker(max_tokens=100)
    
    # Create a test response that will need chunking
    test_response = """# Search Results

## 1. First Item
This is the first item with some content that takes up space.
**Authors:** John Doe, Jane Smith
**Abstract:** This is a long abstract that contains important information about the research...

## 2. Second Item  
This is the second item with more content.
**Authors:** Bob Johnson
**Abstract:** Another abstract with details...

## 3. Third Item
Yet another item with content.
**Authors:** Alice Williams
**Abstract:** More research details here...
"""
    
    # Test if chunking is needed
    should_chunk = chunker.should_chunk(test_response)
    print(f"Should chunk response: {should_chunk}")
    
    if should_chunk:
        # Chunk the response
        result = chunker.chunk_response(test_response, context={"type": "test"})
        
        print(f"Response chunked into {result['total_chunks']} chunks")
        print(f"Total tokens: {result['total_tokens']}")
        print(f"Continuation token: {result.get('continuation_token')}")
        print(f"\nFirst chunk preview (first 200 chars):")
        print(result['content'][:200] + "...")
        
        # Test getting next chunk
        if result.get('continuation_token'):
            print(f"\nGetting next chunk with token: {result['continuation_token']}")
            next_chunk = chunker.get_next_chunk(result['continuation_token'])
            
            if 'error' not in next_chunk:
                print(f"Got chunk {next_chunk['current_chunk'] + 1} of {next_chunk['total_chunks']}")
                print(f"Next continuation token: {next_chunk.get('continuation_token')}")
                print(f"Chunk preview (first 200 chars):")
                print(next_chunk['content'][:200] + "...")
    
    print()

def test_large_response():
    """Test with a large response that simulates real Zotero data."""
    print("Testing with large Zotero-like response...")
    
    # Create a large response similar to what Zotero might return
    items = []
    for i in range(1, 101):  # 100 items
        items.append(f"""## {i}. Research Paper Title Number {i}
**Type:** journalArticle
**Item Key:** ABCD{i:04d}
**Date:** 2024-{i%12+1:02d}-01
**Authors:** Author One, Author Two, Author Three
**Abstract:** This is a detailed abstract for paper number {i}. It contains important information about the research methodology, findings, and conclusions. The study investigates various aspects of the topic and provides insights that are valuable for future research in this area.
**Tags:** `research` `paper{i}` `2024`
""")
    
    large_response = "# Search Results for 'research'\n\n" + "\n".join(items)
    
    print(f"Created response with {len(large_response)} characters")
    print(f"Estimated tokens: {estimate_tokens(large_response)}")
    
    # Test chunking with default settings
    chunker = ResponseChunker()  # Uses default 20000 token limit
    
    if chunker.should_chunk(large_response):
        result = chunker.chunk_response(large_response, context={"type": "search_results"})
        print(f"Response chunked into {result['total_chunks']} chunks")
        print(f"Chunk sizes (in tokens):")
        
        # Get all chunks to show their sizes
        current_token = result.get('continuation_token')
        chunk_num = 1
        print(f"  Chunk {chunk_num}: ~{estimate_tokens(result['content'])} tokens")
        
        while current_token:
            chunk_num += 1
            next_result = chunker.get_next_chunk(current_token)
            if 'error' not in next_result:
                print(f"  Chunk {chunk_num}: ~{estimate_tokens(next_result['content'])} tokens")
                current_token = next_result.get('continuation_token')
            else:
                break
    else:
        print("Response doesn't need chunking with default settings")
    
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Response Chunking Integration")
    print("=" * 50)
    print()
    
    test_token_estimation()
    test_chunking()
    test_large_response()
    
    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)