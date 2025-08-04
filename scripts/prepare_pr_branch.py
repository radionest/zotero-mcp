#!/usr/bin/env python3
"""
Script to prepare feature branches for upstream PR submission.

This script:
1. Creates a clean branch from a feature branch
2. Removes all fork-specific code and identifiers
3. Ensures the branch is ready for upstream submission
"""

import argparse
import subprocess
import sys
import os
import re
from pathlib import Path


def run_command(cmd: list, check=True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def remove_feature_flags(repo_root: Path) -> list:
    """Remove feature flag imports and usage from Python files."""
    modified_files = []
    
    # Patterns to remove
    patterns = [
        # Feature flag imports
        r'# Try to import feature flags.*?\n(?:.*?\n)*?def is_feature_enabled.*?return False\n',
        r'try:\n\s*from zotero_mcp\.feature_flags import.*?\nexcept ImportError:.*?\n(?:.*?\n)*?\s*pass\n',
        r'from zotero_mcp\.feature_flags import.*?\n',
        
        # Feature flag usage
        r'if is_feature_enabled\(.*?\):.*?\n(?:\s+.*?\n)*',
        
        # FORK-ONLY comments and functions
        r'# FORK-ONLY:.*?\n',
        r'def \w+\(.*?\):\n\s*"""[^"]*FORK-ONLY[^"]*""".*?\n(?:.*?\n)*?(?=\n(?:def|class|\Z))',
        
        # Fork identifiers
        r'-radiofork',
    ]
    
    # Find all Python files
    for py_file in repo_root.rglob("*.py"):
        if ".git" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        original_content = py_file.read_text()
        content = original_content
        
        # Apply patterns
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Clean up extra blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        if content != original_content:
            py_file.write_text(content)
            modified_files.append(py_file)
            print(f"  Modified: {py_file.relative_to(repo_root)}")
    
    return modified_files


def remove_fork_specific_files(repo_root: Path) -> list:
    """Remove fork-specific files that should never go upstream."""
    removed_files = []
    
    fork_files = [
        "src/zotero_mcp/feature_flags.py",
        "config_local.py",
        "test_rate_limiter.py",  # If it's a fork-only test
    ]
    
    for file_path in fork_files:
        full_path = repo_root / file_path
        if full_path.exists():
            full_path.unlink()
            removed_files.append(full_path)
            print(f"  Removed: {file_path}")
    
    return removed_files


def restore_upstream_code(repo_root: Path, feature_branch: str) -> None:
    """Restore any upstream code that was modified for feature flags."""
    # Map feature branches to their specific restorations
    restorations = {
        "hybrid_zotero_connector": [
            # Restore get_zotero_client to not use hybrid
            ("src/zotero_mcp/client.py", [
                (r'def get_zotero_client\(\) -> Union\[zotero\.Zotero, Any\]:.*?'
                 r'return HybridZoteroClient\(local_client=local_client, web_client=web_client\)',
                 '''def get_zotero_client() -> zotero.Zotero:
    """
    Get authenticated Zotero client using environment variables.
    
    Returns:
        A configured Zotero client instance.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
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
    )''', re.DOTALL),
            ]),
            # Remove _get_hybrid_client function
            ("src/zotero_mcp/client.py", [
                (r'\n\ndef _get_hybrid_client\(\):.*?return HybridZoteroClient\(.*?\)', '', re.DOTALL),
            ]),
            # Remove hybrid imports from server.py
            ("src/zotero_mcp/server.py", [
                (r'from zotero_mcp\.client import.*?get_hybrid_zotero_client.*?\n',
                 'from zotero_mcp.client import (\n    AttachmentDetails,\n    convert_to_markdown,\n    format_item_metadata,\n    generate_bibtex,\n    get_attachment_details,\n    get_zotero_client,\n)\n'),
                # Replace all get_hybrid_zotero_client calls
                (r'get_hybrid_zotero_client\(\)', 'get_zotero_client()'),
            ]),
        ],
        "rate_limiter": [
            # Remove rate limiter wrapper function
            ("src/zotero_mcp/server.py", [
                (r'\n\ndef _get_zotero_client_with_features\(\):.*?return client', '', re.DOTALL),
                # Replace all _get_zotero_client_with_features calls
                (r'_get_zotero_client_with_features\(\)', 'get_zotero_client()'),
            ]),
            # Remove rate limiter imports
            ("src/zotero_mcp/server.py", [
                (r'from zotero_mcp\.rate_limiter import.*?\n', ''),
            ]),
            ("src/zotero_mcp/client.py", [
                (r'from \.rate_limiter import.*?\n', ''),
                (r'# Check if zot is already rate-limited.*?rate_limited_zot = RateLimitedZoteroClient\(zot\).*?children = rate_limited_zot\.children\(item_key\)',
                 'children = zot.children(item_key)', re.DOTALL),
            ]),
        ],
        "webdav": [
            # Remove WebDAV storage function
            ("src/zotero_mcp/client.py", [
                (r'\n\ndef get_storage_backend\(\) -> Optional\[Any\]:.*?return None', '', re.DOTALL),
            ]),
            # Remove WebDAV imports
            ("src/zotero_mcp/client.py", [
                (r'from zotero_mcp\.storage import.*?\n', ''),
            ]),
            # Remove WebDAV storage check from server.py
            ("src/zotero_mcp/server.py", [
                (r'# Try storage backend first if WebDAV feature is enabled.*?'
                 r'return f"{metadata}\\n\\n---\\n\\n## Full Text\\n\\n{converted_text}"\n\s*'
                 r'# Fall back to direct download from Zotero\n\s*'
                 r'ctx\.info\("Trying direct download from Zotero"\)',
                 '# If we couldn\'t get indexed full text, try to download and convert the file\n'
                 '        ctx.info("Trying direct download from Zotero")', re.DOTALL),
            ]),
        ],
    }
    
    if feature_branch in restorations:
        for file_path, replacements in restorations[feature_branch]:
            full_path = repo_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                for pattern, replacement, *flags in replacements:
                    flag = flags[0] if flags else 0
                    content = re.sub(pattern, replacement, content, flags=flag)
                full_path.write_text(content)
                print(f"  Restored: {file_path}")


def main():
    parser = argparse.ArgumentParser(description="Prepare feature branch for upstream PR")
    parser.add_argument("feature_branch", help="Name of the feature branch to prepare")
    parser.add_argument("--no-push", action="store_true", help="Don't push the cleaned branch")
    args = parser.parse_args()
    
    # Get repo root
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)
    
    # Ensure we're in a git repo
    result = run_command(["git", "rev-parse", "--git-dir"], check=False)
    if result.returncode != 0:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Check if feature branch exists
    result = run_command(["git", "show-ref", f"refs/heads/{args.feature_branch}"], check=False)
    if result.returncode != 0:
        print(f"Error: Feature branch '{args.feature_branch}' does not exist")
        sys.exit(1)
    
    # Create clean branch name
    clean_branch = f"pr-clean/{args.feature_branch}"
    
    print(f"\n=== Preparing clean PR branch from '{args.feature_branch}' ===\n")
    
    # Create and checkout clean branch
    print(f"Creating clean branch: {clean_branch}")
    run_command(["git", "checkout", "-B", clean_branch, args.feature_branch])
    
    # Remove feature flags
    print("\nRemoving feature flags...")
    modified_files = remove_feature_flags(repo_root)
    
    # Remove fork-specific files
    print("\nRemoving fork-specific files...")
    removed_files = remove_fork_specific_files(repo_root)
    
    # Restore upstream code patterns
    print("\nRestoring upstream code patterns...")
    restore_upstream_code(repo_root, args.feature_branch)
    
    # Run Black formatter
    print("\nRunning Black formatter...")
    run_command(["black", "src/zotero_mcp/"], check=False)
    
    # Stage all changes
    if modified_files or removed_files:
        print("\nStaging changes...")
        run_command(["git", "add", "-A"])
        
        # Commit changes
        commit_msg = f"chore: remove fork-specific code for upstream PR\n\nPrepared {args.feature_branch} for upstream submission by:\n- Removing feature flags and fork-only code\n- Removing fork-specific files\n- Restoring upstream code patterns\n- Running Black formatter"
        run_command(["git", "commit", "-m", commit_msg])
        print("\nCommitted changes")
    else:
        print("\nNo changes needed - branch is already clean")
    
    # Show what needs to be done next
    print(f"\n=== Branch '{clean_branch}' is ready for upstream PR ===\n")
    print("Next steps:")
    print(f"1. Review the changes: git diff {args.feature_branch}..{clean_branch}")
    print(f"2. Test the cleaned branch thoroughly")
    print(f"3. Rebase against upstream/main: git rebase upstream/main")
    print(f"4. Force push if needed: git push -f origin {clean_branch}")
    print(f"5. Create PR from {clean_branch} to upstream repository")
    
    if not args.no_push:
        print(f"\nPushing {clean_branch} to origin...")
        run_command(["git", "push", "-u", "origin", clean_branch])


if __name__ == "__main__":
    main()