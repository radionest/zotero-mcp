"""
Factory for creating attachment storage backends.
"""

from typing import Optional, Dict, Any

from .base import AttachmentStorage
from .webdav import WebDAVStorage
from .yandex import YandexDiskStorage


def create_storage(config: Dict[str, Any]) -> Optional[AttachmentStorage]:
    """
    Create an attachment storage backend from configuration.
    
    Args:
        config: Storage configuration dictionary. Must include a 'type' field
               specifying the storage backend ('webdav' or 'yandex').
               
    Returns:
        AttachmentStorage instance or None if configuration is invalid
        
    Example configurations:
        # WebDAV
        {
            "type": "webdav",
            "url": "https://webdav.example.com",
            "username": "user",
            "password": "pass",
            "root_path": "/zotero"
        }
        
        # Yandex Disk
        {
            "type": "yandex",
            "token": "oauth_token",
            "root_path": "/zotero"
        }
    """
    storage_type = config.get("type", "").lower()
    
    if not storage_type:
        print("Storage configuration must include 'type' field")
        return None
    
    try:
        if storage_type == "webdav":
            return WebDAVStorage(config)
        elif storage_type == "yandex":
            return YandexDiskStorage(config)
        else:
            print(f"Unknown storage type: {storage_type}")
            return None
    except Exception as e:
        print(f"Failed to create storage backend: {e}")
        return None