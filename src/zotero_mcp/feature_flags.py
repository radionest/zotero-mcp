"""
Feature flag system for Zotero-MCP dev branch.
This module is excluded from upstream PRs.
"""

import os
from typing import TypedDict, Optional, Literal, Union


class RateLimiterConfig(TypedDict, total=False):
    """Configuration for rate limiter feature."""
    calls: int
    period: int
    retry_delay: float
    max_retries: int


class WebDAVConfig(TypedDict, total=False):
    """Configuration for WebDAV storage feature."""
    storage_type: Literal["webdav", "yandex"]
    url: str
    username: str
    password: str
    root_path: str
    verify_ssl: bool
    token: str  # For Yandex


class HybridClientConfig(TypedDict, total=False):
    """Configuration for hybrid client feature."""
    prefer_local: bool
    fallback_enabled: bool
    operation_routing: dict[str, Literal["local", "web", "auto"]]


class FeatureConfig(TypedDict):
    """Complete feature configuration."""
    enabled: bool
    rate_limiter: Optional[RateLimiterConfig]
    webdav: Optional[WebDAVConfig]
    hybrid_client: Optional[HybridClientConfig]


# Feature flag names
FEATURE_HYBRID_CLIENT = "ZOTERO_HYBRID_CLIENT"
FEATURE_RATE_LIMITER = "ZOTERO_RATE_LIMITER"
FEATURE_WEBDAV_STORAGE = "ZOTERO_WEBDAV_STORAGE"

# All available features
AVAILABLE_FEATURES = {
    FEATURE_HYBRID_CLIENT,
    FEATURE_RATE_LIMITER,
    FEATURE_WEBDAV_STORAGE,
}


def _parse_bool(value: str) -> bool:
    """Parse boolean from environment variable."""
    return value.lower() in ("true", "yes", "1", "on")


def _get_rate_limiter_config() -> RateLimiterConfig:
    """Get rate limiter configuration from environment."""
    config: RateLimiterConfig = {}
    
    if calls := os.getenv("ZOTERO_RATE_LIMIT_CALLS"):
        config["calls"] = int(calls)
    if period := os.getenv("ZOTERO_RATE_LIMIT_PERIOD"):
        config["period"] = int(period)
    if retry_delay := os.getenv("ZOTERO_RATE_LIMIT_RETRY_DELAY"):
        config["retry_delay"] = float(retry_delay)
    if max_retries := os.getenv("ZOTERO_RATE_LIMIT_MAX_RETRIES"):
        config["max_retries"] = int(max_retries)
    
    return config


def _get_webdav_config() -> WebDAVConfig:
    """Get WebDAV configuration from environment."""
    config: WebDAVConfig = {}
    
    storage_type = os.getenv("ZOTERO_STORAGE_TYPE", "webdav")
    if storage_type in ("webdav", "yandex"):
        config["storage_type"] = storage_type
    
    if storage_type == "webdav":
        if url := os.getenv("ZOTERO_WEBDAV_URL"):
            config["url"] = url
        if username := os.getenv("ZOTERO_WEBDAV_USERNAME"):
            config["username"] = username
        if password := os.getenv("ZOTERO_WEBDAV_PASSWORD"):
            config["password"] = password
        if verify_ssl := os.getenv("ZOTERO_WEBDAV_VERIFY_SSL"):
            config["verify_ssl"] = _parse_bool(verify_ssl)
    else:  # yandex
        if token := os.getenv("ZOTERO_YANDEX_TOKEN"):
            config["token"] = token
    
    if root_path := os.getenv("ZOTERO_WEBDAV_ROOT_PATH", "ZOTERO_YANDEX_ROOT_PATH"):
        config["root_path"] = root_path
    
    return config


def _get_hybrid_client_config() -> HybridClientConfig:
    """Get hybrid client configuration from environment."""
    config: HybridClientConfig = {}
    
    if prefer_local := os.getenv("ZOTERO_HYBRID_PREFER_LOCAL"):
        config["prefer_local"] = _parse_bool(prefer_local)
    if fallback := os.getenv("ZOTERO_HYBRID_FALLBACK_ENABLED"):
        config["fallback_enabled"] = _parse_bool(fallback)
    
    # Parse operation routing if provided
    routing = {}
    for op in ["read", "write", "search", "attachment"]:
        if route := os.getenv(f"ZOTERO_HYBRID_ROUTE_{op.upper()}"):
            if route in ("local", "web", "auto"):
                routing[op] = route
    
    if routing:
        config["operation_routing"] = routing
    
    return config


def is_feature_enabled(feature: str) -> bool:
    """
    Check if a feature is enabled via environment variable.
    
    Args:
        feature: Feature name (e.g., "ZOTERO_HYBRID_CLIENT")
        
    Returns:
        True if the feature is enabled, False otherwise.
    """
    if feature not in AVAILABLE_FEATURES:
        return False
    
    value = os.getenv(feature, "false")
    return _parse_bool(value)


def get_feature_config(feature: str) -> Optional[Union[RateLimiterConfig, WebDAVConfig, HybridClientConfig]]:
    """
    Get configuration for a specific feature.
    
    Args:
        feature: Feature name
        
    Returns:
        Feature-specific configuration or None if not enabled.
    """
    if not is_feature_enabled(feature):
        return None
    
    if feature == FEATURE_RATE_LIMITER:
        return _get_rate_limiter_config()
    elif feature == FEATURE_WEBDAV_STORAGE:
        return _get_webdav_config()
    elif feature == FEATURE_HYBRID_CLIENT:
        return _get_hybrid_client_config()
    
    return None


def get_all_features() -> FeatureConfig:
    """
    Get complete feature configuration.
    
    Returns:
        Dictionary with all feature states and configurations.
    """
    return {
        "enabled": any(is_feature_enabled(f) for f in AVAILABLE_FEATURES),
        "rate_limiter": get_feature_config(FEATURE_RATE_LIMITER) if is_feature_enabled(FEATURE_RATE_LIMITER) else None,
        "webdav": get_feature_config(FEATURE_WEBDAV_STORAGE) if is_feature_enabled(FEATURE_WEBDAV_STORAGE) else None,
        "hybrid_client": get_feature_config(FEATURE_HYBRID_CLIENT) if is_feature_enabled(FEATURE_HYBRID_CLIENT) else None,
    }


# Convenience functions for common checks
def is_hybrid_client_enabled() -> bool:
    """Check if hybrid client is enabled."""
    return is_feature_enabled(FEATURE_HYBRID_CLIENT)


def is_rate_limiter_enabled() -> bool:
    """Check if rate limiter is enabled."""
    return is_feature_enabled(FEATURE_RATE_LIMITER)


def is_webdav_enabled() -> bool:
    """Check if WebDAV storage is enabled."""
    return is_feature_enabled(FEATURE_WEBDAV_STORAGE)