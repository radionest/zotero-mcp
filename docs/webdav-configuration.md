# WebDAV Configuration for Zotero Attachments

This guide explains how to configure zotero-mcp to retrieve attachments from WebDAV servers, including Yandex Disk.

## Overview

zotero-mcp supports retrieving Zotero attachments from remote WebDAV servers. This is useful when your Zotero attachments are synced to a cloud storage service that supports WebDAV protocol.

## Supported Storage Types

1. **Generic WebDAV** - Any WebDAV-compatible server
2. **Yandex Disk** - Specialized support for Yandex Disk with OAuth authentication

## Configuration

Configuration is done through environment variables. Add these to your `.env` file:

### Generic WebDAV Configuration

```bash
# Storage type
ZOTERO_STORAGE_TYPE=webdav

# WebDAV server URL
ZOTERO_WEBDAV_URL=https://webdav.example.com

# Authentication (optional for some servers)
ZOTERO_WEBDAV_USERNAME=your_username
ZOTERO_WEBDAV_PASSWORD=your_password

# Path to Zotero folder on WebDAV server (default: /zotero)
ZOTERO_WEBDAV_ROOT_PATH=/path/to/zotero

# SSL verification (default: true)
ZOTERO_WEBDAV_VERIFY_SSL=true
```

### Yandex Disk Configuration

```bash
# Storage type
ZOTERO_STORAGE_TYPE=yandex

# OAuth token for Yandex Disk
ZOTERO_YANDEX_TOKEN=your_oauth_token

# Path to Zotero folder (default: /zotero)
ZOTERO_YANDEX_ROOT_PATH=/zotero
```

#### Getting Yandex Disk OAuth Token

1. Go to https://oauth.yandex.com/
2. Create a new application
3. Request permissions for `cloud_api:disk.read`
4. Get your OAuth token

## How It Works

1. When you request an attachment's full text, zotero-mcp will:
   - First try to get the text from Zotero's full-text index
   - If not available, check if a WebDAV storage backend is configured
   - If configured, attempt to download the attachment from WebDAV
   - Fall back to direct download from Zotero if WebDAV fails

2. Attachments are expected to be stored as:
   - ZIP files named by their attachment key (e.g., `ABCD1234.zip`)
   - The ZIP should contain the actual attachment file (PDF, etc.)

## Directory Structure

### Generic WebDAV
```
/zotero/
├── ABCD1234.zip
├── EFGH5678.zip
└── ...
```

### Yandex Disk
```
/zotero/
├── ABCD1234.zip
├── EFGH5678.zip
└── ...
```

## Troubleshooting

### Connection Issues

Test your configuration by checking if the storage backend can connect:

```python
from zotero_mcp.client import get_storage_backend

storage = get_storage_backend()
if storage:
    print(f"Storage type: {storage.get_storage_info()['type']}")
    print(f"Connected: {storage.test_connection()}")
else:
    print("No storage backend configured")
```

### Common Problems

1. **SSL Certificate Errors**: Set `ZOTERO_WEBDAV_VERIFY_SSL=false` (not recommended for production)
2. **Authentication Failed**: Check your credentials or OAuth token
3. **Path Not Found**: Ensure the root path exists on your WebDAV server
4. **Attachment Not Found**: Verify the attachment exists as a ZIP file with the correct name

## Security Considerations

1. Store credentials securely - use environment variables or secure credential storage
2. Use HTTPS for WebDAV connections
3. For Yandex Disk, use OAuth tokens with minimal required permissions
4. Consider using read-only access if you don't need to upload attachments