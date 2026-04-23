"""
Zotero client wrapper for MCP server.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from markitdown import MarkItDown
from pyzotero import zotero

from zotero_mcp.utils import format_creators

# Try to import feature flags (fork-only)
try:
    from zotero_mcp.feature_flags import (
        is_feature_enabled,
        get_feature_config,
        FEATURE_HYBRID_CLIENT,
        FEATURE_RATE_LIMITER,
        FEATURE_WEBDAV_STORAGE,
    )
except ImportError:
    # Feature flags not available - we're in upstream
    def is_feature_enabled(feature: str) -> bool:
        return False
    
    def get_feature_config(feature: str) -> Optional[Dict[str, Any]]:
        return None
    
    # Feature constants for consistency
    FEATURE_HYBRID_CLIENT = "ZOTERO_HYBRID_CLIENT"
    FEATURE_RATE_LIMITER = "ZOTERO_RATE_LIMITER"
    FEATURE_WEBDAV_STORAGE = "ZOTERO_WEBDAV_STORAGE"

# Load environment variables
load_dotenv()


@dataclass
class AttachmentDetails:
    """Details about a Zotero attachment."""

    key: str
    title: str
    filename: str
    content_type: str


def get_zotero_client() -> Union[zotero.Zotero, Any]:  # Any is for HybridZoteroClient
    """
    Get authenticated Zotero client using environment variables.
    
    Returns:
        A configured Zotero client instance (regular or hybrid based on feature flag).
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Check if hybrid client feature is enabled
    if is_feature_enabled(FEATURE_HYBRID_CLIENT):
        try:
            from zotero_mcp.hybrid_client import HybridZoteroClient
            return _get_hybrid_client()
        except ImportError:
            # Hybrid client not available, fall back to regular
            pass
    
    # Regular client logic
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user")
    api_key = os.getenv("ZOTERO_API_KEY")
    local = os.getenv("ZOTERO_LOCAL", "").lower() in ["true", "yes", "1"]

    # For local API, default to user ID 0 if not specified
    if local and not library_id:
        library_id = "0"

    # For remote API, we need both library_id and api_key
    if not local and not (library_id and api_key):
        raise ValueError(
            "Missing required environment variables. Please set ZOTERO_LIBRARY_ID and ZOTERO_API_KEY, "
            "or use ZOTERO_LOCAL=true for local Zotero instance."
        )

    return zotero.Zotero(
        library_id=library_id,
        library_type=library_type,
        api_key=api_key,
        local=local,
    )


def _get_hybrid_client():
    """
    Helper function to create hybrid client when feature is enabled.
    FORK-ONLY: This function is only used when ZOTERO_HYBRID_CLIENT flag is enabled.
    
    Returns:
        HybridZoteroClient instance
    """
    from zotero_mcp.hybrid_client import HybridZoteroClient
    
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user")
    api_key = os.getenv("ZOTERO_API_KEY")
    use_local = os.getenv("ZOTERO_LOCAL", "").lower() in ["true", "yes", "1"]
    
    local_client = None
    web_client = None
    
    # Try to create local client
    if use_local:
        try:
            local_lib_id = library_id or "0"
            local_client = zotero.Zotero(
                library_id=local_lib_id,
                library_type=library_type,
                api_key=None,
                local=True,
            )
        except Exception as e:
            print('Error while intialization of local client',e)
            pass
    
    # Try to create web client
    if library_id and api_key:
        try:
            web_client = zotero.Zotero(
                library_id=library_id,
                library_type=library_type,
                api_key=api_key,
                local=False,
            )
        except Exception as e:
            print('Error while intialization of web client',e)
            pass
    
    if not local_client and not web_client:
        
        raise ValueError(
            "Could not create any Zotero client. Please check your configuration."
        )
    
    return HybridZoteroClient(local_client=local_client, web_client=web_client)


def get_hybrid_zotero_client():
    """
    Get a hybrid Zotero client that uses both local and web APIs.
    This is a wrapper that respects feature flags.
    
    Returns:
        Either a HybridZoteroClient or regular Zotero client based on configuration.
    """
    # If hybrid client feature is enabled, use the internal helper
    if is_feature_enabled(FEATURE_HYBRID_CLIENT):
        return _get_hybrid_client()
    
    # Otherwise, return regular client
    return get_zotero_client()


def format_item_metadata(item: Dict[str, Any], include_abstract: bool = True) -> str:
    """
    Format a Zotero item's metadata as markdown.
    
    Args:
        item: A Zotero item dictionary.
        include_abstract: Whether to include the abstract in the output.
        
    Returns:
        Markdown-formatted metadata.
    """
    data = item.get("data", {})
    item_type = data.get("itemType", "unknown")
    
    # Basic information
    lines = [
        f"# {data.get('title', 'Untitled')}",
        f"**Type:** {item_type}",
        f"**Item Key:** {data.get('key')}",
    ]
    
    # Date
    if date := data.get("date"):
        lines.append(f"**Date:** {date}")
    
    # Authors/Creators
    if creators := data.get("creators", []):
        lines.append(f"**Authors:** {format_creators(creators)}")
    
    # Publication details based on item type
    if item_type == "journalArticle":
        if journal := data.get("publicationTitle"):
            journal_info = f"**Journal:** {journal}"
            if volume := data.get("volume"):
                journal_info += f", Volume {volume}"
            if issue := data.get("issue"):
                journal_info += f", Issue {issue}"
            if pages := data.get("pages"):
                journal_info += f", Pages {pages}"
            lines.append(journal_info)
    elif item_type == "book":
        if publisher := data.get("publisher"):
            book_info = f"**Publisher:** {publisher}"
            if place := data.get("place"):
                book_info += f", {place}"
            lines.append(book_info)
    
    # DOI and URL
    if doi := data.get("DOI"):
        lines.append(f"**DOI:** {doi}")
    if url := data.get("url"):
        lines.append(f"**URL:** {url}")
    
    # Tags
    if tags := data.get("tags"):
        tag_list = [f"`{tag['tag']}`" for tag in tags]
        if tag_list:
            lines.append(f"**Tags:** {' '.join(tag_list)}")
    
    # Abstract
    if include_abstract and (abstract := data.get("abstractNote")):
        lines.extend(["", "## Abstract", abstract])
    
    # Collections
    if collections := data.get("collections", []):
        if collections:
            lines.append(f"**Collections:** {len(collections)} collections")
    
    # Notes - this requires additional API calls, so we just indicate if there are notes
    if "meta" in item and item["meta"].get("numChildren", 0) > 0:
        lines.append(f"**Notes/Attachments:** {item['meta']['numChildren']}")
    
    return "\n\n".join(lines)


def generate_bibtex(item: Dict[str, Any]) -> str:
    """
    Generate BibTeX format for a Zotero item.
    
    Args:
        item: Zotero item data
    
    Returns:
        BibTeX formatted string
    """
    data = item.get("data", {})
    item_key = data.get("key")
    
    # Try Better BibTeX first
    try:
        from zotero_mcp.better_bibtex_client import ZoteroBetterBibTexAPI
        bibtex = ZoteroBetterBibTexAPI()
        
        if bibtex.is_zotero_running():
            return bibtex.export_bibtex(item_key)
    
    except Exception:
        # Continue to fallback method if Better BibTeX fails
        pass
    
    # Fallback to basic BibTeX generation
    item_type = data.get("itemType", "misc")
    
    if item_type in ["attachment", "note"]:
        raise ValueError(f"Cannot export BibTeX for item type '{item_type}'")
    
    # Map Zotero item types to BibTeX types
    type_map = {
        "journalArticle": "article",
        "book": "book", 
        "bookSection": "incollection",
        "conferencePaper": "inproceedings",
        "thesis": "phdthesis",
        "report": "techreport",
        "webpage": "misc",
        "manuscript": "unpublished"
    }
    
    # Create citation key
    creators = data.get("creators", [])
    author = ""
    if creators:
        first = creators[0]
        author = first.get("lastName", first.get("name", "").split()[-1] if first.get("name") else "").replace(" ", "")
    
    year = data.get("date", "")[:4] if data.get("date") else "nodate"
    cite_key = f"{author}{year}_{item_key}"
    
    # Build BibTeX entry
    bib_type = type_map.get(item_type, "misc")
    lines = [f"@{bib_type}{{{cite_key},"]
    
    # Add fields
    field_mappings = [
        ("title", "title"),
        ("publicationTitle", "journal"),
        ("volume", "volume"),
        ("issue", "number"),
        ("pages", "pages"),
        ("publisher", "publisher"),
        ("DOI", "doi"),
        ("url", "url"),
        ("abstractNote", "abstract")
    ]
    
    for zotero_field, bibtex_field in field_mappings:
        if value := data.get(zotero_field):
            # Escape special characters
            value = value.replace("{", "\\{").replace("}", "\\}")
            lines.append(f'  {bibtex_field} = {{{value}}},')
    
    # Add authors
    if creators:
        authors = []
        for creator in creators:
            if creator.get("creatorType") == "author":
                if "lastName" in creator and "firstName" in creator:
                    authors.append(f"{creator['lastName']}, {creator['firstName']}")
                elif "name" in creator:
                    authors.append(creator["name"])
        if authors:
            lines.append(f'  author = {{{" and ".join(authors)}}},')
    
    # Add year
    if year != "nodate":
        lines.append(f'  year = {{{year}}},')
    
    # Remove trailing comma from last field and close entry
    if lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    
    return "\n".join(lines)


def get_attachment_details(
    zot: Union[zotero.Zotero, Any], item: Dict[str, Any]
) -> Optional[AttachmentDetails]:
    """
    Get attachment details for a Zotero item, finding the most relevant attachment.
    
    Args:
        zot: A Zotero client instance (may be wrapped with rate limiter).
        item: A Zotero item dictionary.
        
    Returns:
        AttachmentDetails if found, None otherwise.
    """
    data = item.get("data", {})
    item_type = data.get("itemType")
    item_key = data.get("key")

    # Direct attachment
    if item_type == "attachment":
        return AttachmentDetails(
            key=item_key,
            title=data.get("title", "Untitled"),
            filename=data.get("filename", ""),
            content_type=data.get("contentType", ""),
        )

    # For regular items, look for child attachments
    try:
        # Apply rate limiting if feature is enabled
        if is_feature_enabled(FEATURE_RATE_LIMITER) and not hasattr(zot, '_client'):
            try:
                from zotero_mcp.rate_limiter import RateLimitedZoteroClient
                zot = RateLimitedZoteroClient(zot)
            except ImportError:
                # Rate limiter not available, continue without it
                pass
        
        children = zot.children(item_key)
        
        # Group attachments by content type
        pdfs = []
        htmls = []
        others = []

        for child in children:
            child_data = child.get("data", {})
            if child_data.get("itemType") == "attachment":
                content_type = child_data.get("contentType", "")
                filename = child_data.get("filename", "")
                title = child_data.get("title", "Untitled")
                key = child.get("key", "")
                
                # Use MD5 as proxy for size (longer MD5 usually means larger file)
                size_proxy = len(child_data.get("md5", ""))
                
                attachment = (key, title, filename, content_type, size_proxy)
                
                if content_type == "application/pdf":
                    pdfs.append(attachment)
                elif content_type.startswith("text/html"):
                    htmls.append(attachment)
                else:
                    others.append(attachment)

        # Return first match in priority order (PDF > HTML > other)
        # Sort each category by size (descending) to get largest/most complete file
        for category in [pdfs, htmls, others]:
            if category:
                category.sort(key=lambda x: x[4], reverse=True)
                key, title, filename, content_type, _ = category[0]
                return AttachmentDetails(
                    key=key,
                    title=title,
                    filename=filename,
                    content_type=content_type,
                )
    except Exception:
        pass

    return None


def get_all_attachment_details(
    zot: Union[zotero.Zotero, Any], item: Dict[str, Any]
) -> List[AttachmentDetails]:
    """
    Get all attachment details for a Zotero item, sorted by priority.

    Returns attachments in priority order: PDFs first (largest to smallest),
    then HTML, then other types.
    """
    data = item.get("data", {})
    item_type = data.get("itemType")
    item_key = data.get("key")

    if item_type == "attachment":
        return [AttachmentDetails(
            key=item_key,
            title=data.get("title", "Untitled"),
            filename=data.get("filename", ""),
            content_type=data.get("contentType", ""),
        )]

    try:
        if is_feature_enabled(FEATURE_RATE_LIMITER) and not hasattr(zot, '_client'):
            try:
                from zotero_mcp.rate_limiter import RateLimitedZoteroClient
                zot = RateLimitedZoteroClient(zot)
            except ImportError:
                pass

        children = zot.children(item_key)

        pdfs = []
        htmls = []
        others = []

        for child in children:
            child_data = child.get("data", {})
            if child_data.get("itemType") == "attachment":
                content_type = child_data.get("contentType", "")
                filename = child_data.get("filename", "")
                title = child_data.get("title", "Untitled")
                key = child.get("key", "")
                size_proxy = len(child_data.get("md5", ""))

                attachment = (key, title, filename, content_type, size_proxy)

                if content_type == "application/pdf":
                    pdfs.append(attachment)
                elif content_type.startswith("text/html"):
                    htmls.append(attachment)
                else:
                    others.append(attachment)

        result = []
        for category in [pdfs, htmls, others]:
            category.sort(key=lambda x: x[4], reverse=True)
            for key, title, filename, content_type, _ in category:
                result.append(AttachmentDetails(
                    key=key,
                    title=title,
                    filename=filename,
                    content_type=content_type,
                ))
        return result
    except Exception:
        pass

    return []


def convert_to_markdown(file_path: Union[str, Path]) -> str:
    """
    Convert a file to markdown using markitdown library.
    
    Args:
        file_path: Path to the file to convert.
        
    Returns:
        Markdown text.
    """
    try:
        md = MarkItDown()
        result = md.convert(str(file_path))
        return result.text_content
    except Exception as e:
        return f"Error converting file to markdown: {str(e)}"


def get_storage_backend() -> Optional[Any]:
    """
    Get the configured attachment storage backend.
    FORK-ONLY: This function is only used when ZOTERO_WEBDAV_STORAGE flag is enabled.
    
    Returns:
        AttachmentStorage instance or None if not configured
    """
    if not is_feature_enabled(FEATURE_WEBDAV_STORAGE):
        return None
    
    try:
        from zotero_mcp.storage import create_storage
        
        # Check for storage configuration in environment variables
        storage_type = os.getenv("ZOTERO_STORAGE_TYPE", "").lower()
        
        if not storage_type:
            return None
        
        config = {"type": storage_type}
        
        if storage_type == "webdav":
            config.update({
                "url": os.getenv("ZOTERO_WEBDAV_URL", ""),
                "username": os.getenv("ZOTERO_WEBDAV_USERNAME", ""),
                "password": os.getenv("ZOTERO_WEBDAV_PASSWORD", ""),
                "root_path": os.getenv("ZOTERO_WEBDAV_ROOT_PATH", "/zotero"),
                "verify_ssl": os.getenv("ZOTERO_WEBDAV_VERIFY_SSL", "true").lower() == "true",
            })
        elif storage_type == "yandex":
            config.update({
                "token": os.getenv("ZOTERO_YANDEX_TOKEN", ""),
                "root_path": os.getenv("ZOTERO_YANDEX_ROOT_PATH", "/zotero"),
            })
        
        return create_storage(config)
    except ImportError:
        # Storage module not available
        return None
