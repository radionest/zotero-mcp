#!/bin/bash

# Helper script to manage Claude files across branches

case "$1" in
    "save")
        # Save Claude files before switching branches
        if [ -f CLAUDE.md ] || [ -d .claude ]; then
            branch_name=$(git symbolic-ref --short HEAD)
            mkdir -p .git/claude-files/"$branch_name"
            [ -f CLAUDE.md ] && cp CLAUDE.md .git/claude-files/"$branch_name"/
            [ -d .claude ] && cp -r .claude .git/claude-files/"$branch_name"/
            echo "Claude files saved for branch: $branch_name"
        fi
        ;;
    
    "restore")
        # Restore Claude files after switching branches
        branch_name=$(git symbolic-ref --short HEAD)
        if [ -d .git/claude-files/"$branch_name" ]; then
            [ -f .git/claude-files/"$branch_name"/CLAUDE.md ] && cp .git/claude-files/"$branch_name"/CLAUDE.md .
            [ -d .git/claude-files/"$branch_name"/.claude ] && cp -r .git/claude-files/"$branch_name"/.claude .
            echo "Claude files restored for branch: $branch_name"
        fi
        ;;
    
    "clean-pr")
        # Create a clean branch for PR without Claude files
        if [ -z "$2" ]; then
            echo "Usage: $0 clean-pr <new-branch-name>"
            exit 1
        fi
        
        # Save current Claude files
        $0 save
        
        # Create new branch
        git checkout -b "$2"
        
        # Remove Claude files
        rm -f CLAUDE.md
        rm -rf .claude
        
        # Stage the removal
        git add -A
        git commit -m "chore: remove Claude-specific files for PR"
        
        echo "Created clean branch '$2' without Claude files"
        ;;
    
    "check")
        # Check if Claude files exist in current branch
        if [ -f CLAUDE.md ] || [ -d .claude ]; then
            echo "Claude files found in current branch:"
            [ -f CLAUDE.md ] && echo "  - CLAUDE.md"
            [ -d .claude ] && echo "  - .claude/"
        else
            echo "No Claude files in current branch"
        fi
        ;;
    
    *)
        echo "Usage: $0 {save|restore|clean-pr|check}"
        echo "  save      - Save Claude files before branch switch"
        echo "  restore   - Restore Claude files after branch switch"
        echo "  clean-pr  - Create a clean branch for PR without Claude files"
        echo "  check     - Check if Claude files exist in current branch"
        exit 1
        ;;
esac