"""
Hybrid Zotero client that intelligently uses both local and web APIs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pyzotero import zotero


class APICapability(Enum):
    """Defines API capabilities"""
    READ_ITEMS = "read_items"
    READ_COLLECTIONS = "read_collections"
    READ_FULL_DATA = "read_full_data"  # Without pagination
    WRITE_ITEMS = "write_items"
    WRITE_NOTES = "write_notes"
    UPDATE_ITEMS = "update_items"
    DELETE_ITEMS = "delete_items"
    READ_FULLTEXT = "read_fulltext"
    READ_CHILDREN = "read_children"
    READ_TAGS = "read_tags"


class ZoteroAPIAdapter(ABC):
    """Base adapter for Zotero API"""
    
    @abstractmethod
    def get_capabilities(self) -> List[APICapability]:
        """Returns list of supported operations"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the API is available"""
        pass
    
    @abstractmethod
    def collections(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get collections"""
        pass
    
    @abstractmethod
    def collection(self, collection_key: str) -> Dict[str, Any]:
        """Get a specific collection"""
        pass
    
    @abstractmethod
    def collection_items(self, collection_key: str, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get items in a collection"""
        pass
    
    @abstractmethod
    def items(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get items"""
        pass
    
    @abstractmethod
    def item(self, item_key: str) -> Dict[str, Any]:
        """Get a specific item"""
        pass
    
    @abstractmethod
    def children(self, item_key: str) -> List[Dict[str, Any]]:
        """Get child items"""
        pass
    
    @abstractmethod
    def tags(self, limit: Optional[int] = None, **kwargs) -> List[str]:
        """Get tags"""
        pass
    
    @abstractmethod
    def add_parameters(self, **kwargs) -> None:
        """Add query parameters"""
        pass
    
    @abstractmethod
    def create_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create items"""
        pass
    
    @abstractmethod
    def update_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item"""
        pass
    
    @abstractmethod
    def delete_item(self, item_key: str) -> bool:
        """Delete an item"""
        pass
    
    @abstractmethod
    def fulltext_item(self, item_key: str) -> Dict[str, Any]:
        """Get fulltext content"""
        pass
    
    @abstractmethod
    def dump(self, item_key: str, filename: str, path: str = '.') -> None:
        """Download an attachment"""
        pass
    
    @abstractmethod
    def everything(self, items_func) -> List[Dict[str, Any]]:
        """Get all results using pagination"""
        pass
    
    @abstractmethod
    def saved_search(self, name: str, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a saved search"""
        pass
    
    @abstractmethod
    def delete_saved_search(self, search_keys: List[str]) -> bool:
        """Delete saved searches"""
        pass


class LocalAPIAdapter(ZoteroAPIAdapter):
    """Adapter for local API"""
    
    def __init__(self, client: zotero.Zotero):
        self.client = client
        self._available = None
        
    def get_capabilities(self) -> List[APICapability]:
        return [
            APICapability.READ_ITEMS,
            APICapability.READ_COLLECTIONS,
            APICapability.READ_FULL_DATA,
            APICapability.READ_FULLTEXT,
            APICapability.READ_CHILDREN,
            APICapability.READ_TAGS,
        ]
    
    def is_available(self) -> bool:
        """Check if local Zotero is running"""
        if self._available is not None:
            return self._available
    
        try:
            # Try a simple operation
            self.client.collections(limit=1)
            self._available = True
        except Exception:
            self._available = False
        
        return self._available
    
    def collections(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        # Local API returns all collections without pagination
        all_collections = self.client.collections(**kwargs)
        if limit:
            return all_collections[:limit]
        return all_collections
    
    def collection(self, collection_key: str) -> Dict[str, Any]:
        return self.client.collection(collection_key)
    
    def collection_items(self, collection_key: str, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        return self.client.collection_items(collection_key, limit=limit, **kwargs)
    
    def items(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        return self.client.items(limit=limit, **kwargs)
    
    def item(self, item_key: str) -> Dict[str, Any]:
        return self.client.item(item_key)
    
    def children(self, item_key: str) -> List[Dict[str, Any]]:
        return self.client.children(item_key)
    
    def tags(self, limit: Optional[int] = None, **kwargs) -> List[str]:
        return self.client.tags(limit=limit, **kwargs)
    
    def add_parameters(self, **kwargs) -> None:
        self.client.add_parameters(**kwargs)
    
    def create_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError("Local API doesn't support write operations")
    
    def update_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Local API doesn't support write operations")
    
    def delete_item(self, item_key: str) -> bool:
        raise NotImplementedError("Local API doesn't support write operations")
    
    def fulltext_item(self, item_key: str) -> Dict[str, Any]:
        return self.client.fulltext_item(item_key)
    
    def dump(self, item_key: str, filename: str, path: str = '.') -> None:
        self.client.dump(item_key, filename=filename, path=path)
    
    def everything(self, items_func) -> List[Dict[str, Any]]:
        return self.client.everything(items_func)
    
    def saved_search(self, name: str, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError("Local API doesn't support saved searches")
    
    def delete_saved_search(self, search_keys: List[str]) -> bool:
        raise NotImplementedError("Local API doesn't support saved searches")


class WebAPIAdapter(ZoteroAPIAdapter):
    """Adapter for web API"""
    
    def __init__(self, client: zotero.Zotero):
        self.client = client
        self._available = None
        
    def get_capabilities(self) -> List[APICapability]:
        return [
            APICapability.READ_ITEMS,
            APICapability.READ_COLLECTIONS,
            APICapability.WRITE_ITEMS,
            APICapability.WRITE_NOTES,
            APICapability.UPDATE_ITEMS,
            APICapability.DELETE_ITEMS,
            APICapability.READ_FULLTEXT,
            APICapability.READ_CHILDREN,
            APICapability.READ_TAGS,
        ]
    
    def is_available(self) -> bool:
        """Check if web API is accessible"""
        if self._available is not None:
            return self._available
            
        try:
            # Try a simple operation
            self.client.collections(limit=1)
            self._available = True
        except Exception:
            self._available = False
        
        return self._available
    
    def collections(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        # Web API requires pagination for large requests
        if limit is None or limit > 100:
            # Collect all collections through pagination
            all_collections = []
            start = 0
            batch_size = 100
            
            while True:
                self.client.add_parameters(limit=batch_size, start=start)
                batch = self.client.collections(**kwargs)
                if not batch:
                    break
                all_collections.extend(batch)
                if len(batch) < batch_size:
                    break
                start += batch_size
                
                # Apply limit if specified
                if limit and len(all_collections) >= limit:
                    return all_collections[:limit]
                
            return all_collections
        else:
            return self.client.collections(limit=limit, **kwargs)
    
    def collection(self, collection_key: str) -> Dict[str, Any]:
        return self.client.collection(collection_key)
    
    def collection_items(self, collection_key: str, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        return self.client.collection_items(collection_key, limit=limit, **kwargs)
    
    def items(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        return self.client.items(limit=limit, **kwargs)
    
    def item(self, item_key: str) -> Dict[str, Any]:
        return self.client.item(item_key)
    
    def children(self, item_key: str) -> List[Dict[str, Any]]:
        return self.client.children(item_key)
    
    def tags(self, limit: Optional[int] = None, **kwargs) -> List[str]:
        return self.client.tags(limit=limit, **kwargs)
    
    def add_parameters(self, **kwargs) -> None:
        self.client.add_parameters(**kwargs)
    
    def create_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.client.create_items(items)
    
    def update_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.update_item(item)
    
    def delete_item(self, item_key: str) -> bool:
        return self.client.delete_item(item_key)
    
    def fulltext_item(self, item_key: str) -> Dict[str, Any]:
        return self.client.fulltext_item(item_key)
    
    def dump(self, item_key: str, filename: str, path: str = '.') -> None:
        self.client.dump(item_key, filename=filename, path=path)
    
    def everything(self, items_func) -> List[Dict[str, Any]]:
        return self.client.everything(items_func)
    
    def saved_search(self, name: str, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.client.saved_search(name, conditions)
    
    def delete_saved_search(self, search_keys: List[str]) -> bool:
        return self.client.delete_saved_search(search_keys)


class HybridZoteroClient:
    """Hybrid client that intelligently uses both APIs"""
    
    def __init__(self, local_client: Optional[zotero.Zotero] = None, 
                 web_client: Optional[zotero.Zotero] = None):
        self.local_adapter = LocalAPIAdapter(local_client) if local_client else None
        self.web_adapter = WebAPIAdapter(web_client) if web_client else None
        
        if not self.local_adapter and not self.web_adapter:
            raise ValueError("At least one client (local or web) must be provided")
        
        # Operation preferences map
        self.operation_preferences = {
            'collections_full': 'local',  # Prefer local for full data
            'collections_limited': 'any',  # Any for limited data
            'create_items': 'web',  # Only web for write
            'update_items': 'web',
            'delete_items': 'web',
            'read_items': 'local',  # Prefer local for reading
            'read_fulltext': 'local',  # Prefer local for fulltext
            'saved_search': 'web',  # Only web supports saved searches
        }
        
        # Track which adapter is currently active for parameter passing
        self._active_adapter = None
    
    def _get_adapter_for_operation(self, operation: str, prefer_local: bool = True) -> ZoteroAPIAdapter:
        """Select appropriate adapter for operation"""
        preference = self.operation_preferences.get(operation, 'any')
        
        # Check availability
        local_available = self.local_adapter and self.local_adapter.is_available()
        web_available = self.web_adapter and self.web_adapter.is_available()
        
        if preference == 'local' and local_available:
            self._active_adapter = self.local_adapter
            return self.local_adapter
        elif preference == 'web' and web_available:
            self._active_adapter = self.web_adapter
            return self.web_adapter
        elif preference == 'any':
            if prefer_local and local_available:
                self._active_adapter = self.local_adapter
                return self.local_adapter
            elif web_available:
                self._active_adapter = self.web_adapter
                return self.web_adapter
            elif local_available:
                self._active_adapter = self.local_adapter
                return self.local_adapter
        
        # Fallback to any available adapter
        if local_available:
            self._active_adapter = self.local_adapter
            return self.local_adapter
        elif web_available:
            self._active_adapter = self.web_adapter
            return self.web_adapter
        
        raise RuntimeError(f"No suitable adapter available for operation: {operation}")
    
    def collections(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Smart API selection for getting collections"""
        if limit is None or limit > 100:
            # For large requests prefer local API
            operation = 'collections_full'
        else:
            operation = 'collections_limited'
            
        adapter = self._get_adapter_for_operation(operation)
        return adapter.collections(limit=limit, **kwargs)
    
    def collection(self, collection_key: str) -> Dict[str, Any]:
        """Get a specific collection"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.collection(collection_key)
    
    def collection_items(self, collection_key: str, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get items in a collection"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.collection_items(collection_key, limit=limit, **kwargs)
    
    def items(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get items with auto API selection"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.items(limit=limit, **kwargs)
    
    def item(self, item_key: str) -> Dict[str, Any]:
        """Get a specific item"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.item(item_key)
    
    def children(self, item_key: str) -> List[Dict[str, Any]]:
        """Get child items"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.children(item_key)
    
    def tags(self, limit: Optional[int] = None, **kwargs) -> List[str]:
        """Get tags"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.tags(limit=limit, **kwargs)
    
    def add_parameters(self, **kwargs) -> None:
        """Add query parameters to the active adapter"""
        if self._active_adapter:
            self._active_adapter.add_parameters(**kwargs)
        else:
            # If no active adapter, try to add to both
            if self.local_adapter:
                self.local_adapter.add_parameters(**kwargs)
            if self.web_adapter:
                self.web_adapter.add_parameters(**kwargs)
    
    def create_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create items through web API"""
        adapter = self._get_adapter_for_operation('create_items')
        return adapter.create_items(items)
    
    def update_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item through web API"""
        adapter = self._get_adapter_for_operation('update_items')
        return adapter.update_item(item)
    
    def delete_item(self, item_key: str) -> bool:
        """Delete an item through web API"""
        adapter = self._get_adapter_for_operation('delete_items')
        return adapter.delete_item(item_key)
    
    def fulltext_item(self, item_key: str) -> Dict[str, Any]:
        """Get fulltext content"""
        adapter = self._get_adapter_for_operation('read_fulltext')
        return adapter.fulltext_item(item_key)
    
    def dump(self, item_key: str, filename: str, path: str = '.') -> None:
        """Download an attachment"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.dump(item_key, filename=filename, path=path)
    
    def everything(self, items_func) -> List[Dict[str, Any]]:
        """Get all results using pagination"""
        adapter = self._get_adapter_for_operation('read_items')
        return adapter.everything(items_func)
    
    def saved_search(self, name: str, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a saved search (web API only)"""
        adapter = self._get_adapter_for_operation('saved_search')
        return adapter.saved_search(name, conditions)
    
    def delete_saved_search(self, search_keys: List[str]) -> bool:
        """Delete saved searches (web API only)"""
        adapter = self._get_adapter_for_operation('saved_search')
        return adapter.delete_saved_search(search_keys)
    
    def get_capabilities(self) -> Dict[str, List[APICapability]]:
        """Get capabilities of available adapters"""
        capabilities = {}
        
        if self.local_adapter and self.local_adapter.is_available():
            capabilities['local'] = self.local_adapter.get_capabilities()
        
        if self.web_adapter and self.web_adapter.is_available():
            capabilities['web'] = self.web_adapter.get_capabilities()
            
        return capabilities