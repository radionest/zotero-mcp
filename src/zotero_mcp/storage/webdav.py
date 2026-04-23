"""
WebDAV storage backend for Zotero attachments.
"""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

from webdav3.client import Client

from .base import AttachmentStorage


class WebDAVStorage(AttachmentStorage):
    """WebDAV storage backend implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize WebDAV storage with configuration.
        
        Args:
            config: Configuration dictionary with the following structure:
                {
                    "url": "https://webdav.example.com",  # WebDAV endpoint
                    "username": "user",  # Optional for some servers
                    "password": "pass",  # Optional for some servers
                    "root_path": "/remote/path/to/zotero",  # Path to Zotero folder
                    "verify_ssl": True,  # SSL verification (default: True)
                    "timeout": 30  # Request timeout in seconds (default: 30)
                }
        """
        super().__init__(config)
        self.client = self._create_client()
    
    def _validate_config(self) -> None:
        """Validate WebDAV configuration."""
        if not self.config.get("url"):
            raise ValueError("WebDAV configuration requires 'url'")
        
        # Set defaults
        if "verify_ssl" not in self.config:
            self.config["verify_ssl"] = True
        if "timeout" not in self.config:
            self.config["timeout"] = 30
        if "root_path" not in self.config:
            self.config["root_path"] = "/"
    
    def _create_client(self) -> Client:
        """Create WebDAV client instance."""
        webdav_options = {
            "webdav_hostname": self.config["url"],
            "webdav_login": self.config.get("username", ""),
            "webdav_password": self.config.get("password", ""),
            "verify": self.config.get("verify_ssl", True),
            "timeout": self.config.get("timeout", 30),
        }
        return Client(webdav_options)
    
    def get_attachment(self, attachment_key: str, target_path: Optional[Path] = None) -> Optional[Path]:
        """
        Retrieve an attachment from WebDAV server.
        
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
            # Try different possible paths for the attachment
            root_path = self.config.get("root_path", "/").rstrip("/")
            possible_paths = [
                f"{root_path}/{attachment_key}.zip",
                f"{root_path}/storage/{attachment_key}.zip",
                f"{root_path}/{attachment_key}",
                f"{root_path}/storage/{attachment_key}",
            ]
            
            remote_path = None
            for path in possible_paths:
                if self.client.check(path):
                    remote_path = path
                    break
            
            if not remote_path:
                return None
            
            # Download the file
            local_filename = Path(remote_path).name
            local_path = target_path / local_filename
            
            self.client.download_sync(remote_path, str(local_path))
            
            # If it's a zip file, extract it
            if local_path.suffix.lower() == '.zip':
                return self._extract_zip_attachment(local_path, attachment_key, target_path)
            else:
                return local_path
                
        except Exception as e:
            print(f"Error retrieving attachment from WebDAV: {e}")
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
        """Check if an attachment exists on WebDAV server."""
        try:
            root_path = self.config.get("root_path", "/").rstrip("/")
            possible_paths = [
                f"{root_path}/{attachment_key}.zip",
                f"{root_path}/storage/{attachment_key}.zip",
                f"{root_path}/{attachment_key}",
                f"{root_path}/storage/{attachment_key}",
            ]
            
            for path in possible_paths:
                if self.client.check(path):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking attachment existence: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test if the WebDAV connection is working."""
        try:
            root_path = self.config.get("root_path", "/")
            return self.client.check(root_path)
        except Exception as e:
            print(f"WebDAV connection test failed: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the WebDAV storage."""
        info = {
            "type": "webdav",
            "url": self.config.get("url"),
            "root_path": self.config.get("root_path", "/"),
            "connected": False,
        }
        
        try:
            if self.test_connection():
                info["connected"] = True
                # Try to get free space info if available
                root_path = self.config.get("root_path", "/")
                try:
                    free_size = self.client.free(root_path)
                    if free_size:
                        info["free_space_bytes"] = free_size
                except:
                    pass
        except:
            pass
        
        return info