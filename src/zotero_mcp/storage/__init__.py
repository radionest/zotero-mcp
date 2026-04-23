"""
Storage backends for Zotero attachments.
"""

from .base import AttachmentStorage
from .factory import create_storage
from .webdav import WebDAVStorage
from .yandex import YandexDiskStorage

__all__ = ["AttachmentStorage", "create_storage", "WebDAVStorage", "YandexDiskStorage"]