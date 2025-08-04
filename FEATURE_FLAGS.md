# Feature Flags Documentation (Dev Branch Only)

This document describes the experimental feature flags available in the dev branch of the zotero-mcp fork. These features are disabled by default and must be explicitly enabled via environment variables.

**IMPORTANT**: These features are fork-specific and will be removed when preparing branches for upstream PRs.

## Available Feature Flags

### 1. ZOTERO_HYBRID_CLIENT

**Environment Variable**: `ZOTERO_HYBRID_CLIENT=true`

**Description**: Enables the hybrid Zotero client that intelligently switches between local and web APIs based on operation type and availability.

**Benefits**:
- Automatic failover between local and web APIs
- Optimized API selection based on operation type
- Better performance for large data operations using local API
- Write operations automatically use web API

**Usage**:
```bash
export ZOTERO_HYBRID_CLIENT=true
zotero-mcp serve
```

**Branch**: `hybrid_zotero_connector`

### 2. ZOTERO_RATE_LIMITER

**Environment Variable**: `ZOTERO_RATE_LIMITER=true`

**Description**: Adds rate limiting to all Zotero API calls to prevent hitting API quotas.

**Benefits**:
- Prevents API quota exhaustion
- Automatic retry with backoff
- Configurable rate limits
- Especially useful for batch operations

**Usage**:
```bash
export ZOTERO_RATE_LIMITER=true
# Optional: Configure rate limits
export ZOTERO_RATE_LIMIT_CALLS=100
export ZOTERO_RATE_LIMIT_PERIOD=60
zotero-mcp serve
```

**Branch**: `rate_limiter`

### 3. ZOTERO_WEBDAV_STORAGE

**Environment Variable**: `ZOTERO_WEBDAV_STORAGE=true`

**Description**: Enables direct WebDAV storage access for attachments, supporting both standard WebDAV and Yandex.Disk.

**Benefits**:
- Direct attachment access without Zotero API
- Support for custom WebDAV servers
- Yandex.Disk integration
- Faster attachment retrieval

**Configuration**:
```bash
export ZOTERO_WEBDAV_STORAGE=true
export ZOTERO_STORAGE_TYPE=webdav  # or 'yandex'

# For WebDAV:
export ZOTERO_WEBDAV_URL=https://your-webdav-server.com
export ZOTERO_WEBDAV_USERNAME=your-username
export ZOTERO_WEBDAV_PASSWORD=your-password
export ZOTERO_WEBDAV_ROOT_PATH=/zotero
export ZOTERO_WEBDAV_VERIFY_SSL=true

# For Yandex:
export ZOTERO_YANDEX_TOKEN=your-oauth-token
export ZOTERO_YANDEX_ROOT_PATH=/zotero
```

**Branch**: `webdav`

## Using Multiple Features

You can enable multiple features simultaneously:

```bash
export ZOTERO_HYBRID_CLIENT=true
export ZOTERO_RATE_LIMITER=true
export ZOTERO_WEBDAV_STORAGE=true
zotero-mcp serve
```

## Development Workflow

### 1. Enabling Features in Development

Features can be enabled by setting environment variables or creating a `.env` file in the project root:

```bash
# .env file
ZOTERO_HYBRID_CLIENT=true
ZOTERO_RATE_LIMITER=true
ZOTERO_WEBDAV_STORAGE=false
```

### 2. Testing Features

Each feature should be tested independently and in combination:

```bash
# Test individual features
ZOTERO_HYBRID_CLIENT=true pytest tests/
ZOTERO_RATE_LIMITER=true pytest tests/
ZOTERO_WEBDAV_STORAGE=true pytest tests/

# Test combinations
ZOTERO_HYBRID_CLIENT=true ZOTERO_RATE_LIMITER=true pytest tests/
```

### 3. Preparing for Upstream PR

When ready to submit a feature upstream, use the preparation script:

```bash
# Prepare a clean branch without feature flags
./scripts/prepare_pr_branch.py hybrid_zotero_connector

# This creates a clean branch: pr-clean/hybrid_zotero_connector
# Review the changes
git diff hybrid_zotero_connector..pr-clean/hybrid_zotero_connector

# Test the clean branch
git checkout pr-clean/hybrid_zotero_connector
pytest tests/

# Rebase and push
git rebase upstream/main
git push origin pr-clean/hybrid_zotero_connector
```

## Implementation Details

### Feature Flag System

The feature flag system is implemented in `src/zotero_mcp/feature_flags.py` (excluded from upstream):

- All flags default to `false`
- Flags are read from environment variables
- Safe fallback when feature modules are not available
- No performance impact when features are disabled

### Code Organization

Feature-specific code follows these patterns:

1. **Conditional Imports**:
   ```python
   try:
       from zotero_mcp.feature_flags import is_feature_enabled
   except ImportError:
       def is_feature_enabled(feature: str) -> bool:
           return False
   ```

2. **Feature Checks**:
   ```python
   if is_feature_enabled("ZOTERO_HYBRID_CLIENT"):
       # Use hybrid client
   else:
       # Use standard client
   ```

3. **Optional Dependencies**:
   ```python
   if is_feature_enabled("ZOTERO_WEBDAV_STORAGE"):
       try:
           from zotero_mcp.storage import create_storage
           # Use storage backend
       except ImportError:
           # Feature not available
   ```

## Contributing

When adding new experimental features:

1. Add the feature flag to `src/zotero_mcp/feature_flags.py`
2. Document the flag in this file
3. Create a feature branch from `dev`
4. Implement with proper feature flag guards
5. Test with flag enabled and disabled
6. Update the PR preparation script if needed

## Important Notes

- Feature flags are **never** included in upstream PRs
- All feature flag code must be properly guarded
- Features should work correctly when disabled (default behavior)
- The `main` branch should never contain feature flag code
- Use the PR preparation script before submitting upstream