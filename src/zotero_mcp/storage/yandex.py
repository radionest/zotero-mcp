"""
Yandex Disk storage backend for Zotero attachments.
"""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

import yadisk

from .base import AttachmentStorage


class YandexDiskStorage(AttachmentStorage):
    """Yandex Disk storage backend implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Yandex Disk storage with configuration.
        
        Args:
            config: Configuration dictionary with the following structure:
                {
                    "token": "oauth_token",  # OAuth token for Yandex Disk
                    "root_path": "/zotero",  # Path to Zotero folder (default: /zotero)
                }
        """
        super().__init__(config)
        self.client = yadisk.YaDisk(token=self.config["token"])
    
    def _validate_config(self) -> None:
        """Validate Yandex Disk configuration."""
        if not self.config.get("token"):
            raise ValueError("Yandex Disk configuration requires 'token'")
        
        # Set default root path
        if "root_path" not in self.config:
            self.config["root_path"] = "/zotero"
    
    def get_attachment(self, attachment_key: str, target_path: Optional[Path] = None) -> Optional[Path]:
        """
        Retrieve an attachment from Yandex Disk.
        
        Args:
            attachment_key: Zotero attachment key/ID
            target_path: Optional path to save the file. If None, uses temp directory.
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        if target_path is None:
            temp_dir = tempfile.mkdtemp()
            target_path = Path(temp_dir)
        
        try:
            # Yandex stores attachments as zip files named by their key
            root_path = self.config.get("root_path", "/zotero").rstrip("/")
            remote_zip_path = f"{root_path}/{attachment_key}.zip"
            
            # Check if file exists
            if not self.client.exists(remote_zip_path):
                # Try without .zip extension
                remote_path = f"{root_path}/{attachment_key}"
                if not self.client.exists(remote_path):
                    return None
                remote_zip_path = remote_path
            
            # Download the file
            local_filename = Path(remote_zip_path).name
            local_path = target_path / local_filename
            self.client.download(remote_zip_path, str(local_path))
            
            # If it's a zip file, extract it
            if local_path.suffix.lower() == '.zip':
                return self._extract_zip_attachment(local_path, attachment_key, target_path)
            else:
                return local_path
                
        except Exception as e:
            print(f"Error retrieving attachment from Yandex Disk: {e}")
            return None
    
    def _extract_zip_attachment(self, zip_path: Path, attachment_key: str, target_path: Path) -> Optional[Path]:
        """Extract attachment from zip file and return main file path."""
        try:
            extract_dir = target_path / attachment_key
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
            # Find the main file (prefer PDFs)
            files = list(extract_dir.iterdir())
            if not files:
                return None
            
            # Sort files by preference: PDF > other documents > any file
            pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
            doc_files = [f for f in files if f.suffix.lower() in ['.doc', '.docx', '.odt', '.rtf']]
            
            if pdf_files:
                return pdf_files[0]
            elif doc_files:
                return doc_files[0]
            else:
                return files[0]
                
        except Exception as e:
            print(f"Error extracting zip attachment: {e}")
            return None
    
    def exists(self, attachment_key: str) -> bool:
        """Check if an attachment exists on Yandex Disk."""
        try:
            root_path = self.config.get("root_path", "/zotero").rstrip("/")
            # Check both with and without .zip extension
            paths_to_check = [
                f"{root_path}/{attachment_key}.zip",
                f"{root_path}/{attachment_key}"
            ]
            
            for path in paths_to_check:
                if self.client.exists(path):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking attachment existence: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test if the Yandex Disk connection is working."""
        try:
            # Check if we can access the root path
            root_path = self.config.get("root_path", "/zotero")
            return self.client.exists(root_path)
        except Exception as e:
            print(f"Yandex Disk connection test failed: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the Yandex Disk storage."""
        info = {
            "type": "yandex_disk",
            "root_path": self.config.get("root_path", "/zotero"),
            "connected": False,
        }
        
        try:
            if self.test_connection():
                info["connected"] = True
                # Get disk info
                disk_info = self.client.get_disk_info()
                if disk_info:
                    info["total_space_bytes"] = disk_info.total_space
                    info["used_space_bytes"] = disk_info.used_space
                    info["trash_size_bytes"] = disk_info.trash_size
        except Exception as e:
            print(f"Error getting Yandex Disk info: {e}")
        
        return info