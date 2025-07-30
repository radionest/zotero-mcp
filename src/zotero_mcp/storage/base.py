"""
Base abstract class for attachment storage backends.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List


class AttachmentStorage(ABC):
    """Abstract base class for attachment storage implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize storage backend with configuration.
        
        Args:
            config: Storage-specific configuration dictionary
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate configuration for the specific storage backend.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_attachment(self, attachment_key: str, target_path: Optional[Path] = None) -> Optional[Path]:
        """
        Retrieve an attachment from storage.
        
        Args:
            attachment_key: Zotero attachment key/ID
            target_path: Optional path to save the file. If None, uses temp directory.
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        pass
    
    @abstractmethod
    def exists(self, attachment_key: str) -> bool:
        """
        Check if an attachment exists in storage.
        
        Args:
            attachment_key: Zotero attachment key/ID
            
        Returns:
            True if attachment exists, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the storage connection is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
    
    def get_multiple_attachments(self, attachment_keys: List[str], target_dir: Optional[Path] = None) -> Dict[str, Optional[Path]]:
        """
        Retrieve multiple attachments from storage.
        
        Args:
            attachment_keys: List of Zotero attachment keys/IDs
            target_dir: Optional directory to save files. If None, uses temp directory.
            
        Returns:
            Dictionary mapping attachment keys to their downloaded paths (or None if failed)
        """
        results = {}
        for key in attachment_keys:
            results[key] = self.get_attachment(key, target_dir)
        return results
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage backend.
        
        Returns:
            Dictionary with storage information (type, capacity, etc.)
        """
        pass