#!/bin/bash

# Force Wiki Content Sync Script
# This script manually updates the GitHub wiki with content from the repository

set -e

echo "🔄 Force syncing wiki content..."

# Configuration
REPO_URL="https://github.com/happy2234/gopnik"
WIKI_URL="${REPO_URL}.wiki.git"
WIKI_DIR="wiki-temp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📍 Repository: ${REPO_URL}${NC}"
echo -e "${BLUE}📍 Wiki URL: ${WIKI_URL}${NC}"
echo ""

# Check if wiki directory exists in repository
if [ ! -d "wiki" ]; then
    echo -e "${RED}❌ Error: wiki/ directory not found in repository${NC}"
    echo "Make sure you're running this script from the repository root"
    exit 1
fi

# Count wiki files
WIKI_FILES=$(find wiki -name "*.md" | wc -l)
echo -e "${BLUE}📄 Found ${WIKI_FILES} wiki files to sync${NC}"

# Clone wiki repository
echo -e "${YELLOW}🔄 Cloning wiki repository...${NC}"
if [ -d "$WIKI_DIR" ]; then
    rm -rf "$WIKI_DIR"
fi

if git clone "$WIKI_URL" "$WIKI_DIR" 2>/dev/null; then
    echo -e "${GREEN}✅ Wiki repository cloned successfully${NC}"
else
    echo -e "${RED}❌ Failed to clone wiki repository${NC}"
    echo "This usually means:"
    echo "1. Wiki is not enabled in repository settings"
    echo "2. You don't have access to the repository"
    echo "3. The wiki has never been initialized"
    echo ""
    echo "To fix this:"
    echo "1. Go to ${REPO_URL}/settings"
    echo "2. Enable 'Wikis' in the Features section"
    echo "3. Create at least one wiki page manually"
    echo "4. Re-run this script"
    exit 1
fi

cd "$WIKI_DIR"

echo -e "${YELLOW}📝 Updating wiki content...${NC}"

# Track changes
CHANGES_MADE=false

# Copy all wiki files from the main repository
for file in ../wiki/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -e "${BLUE}Processing $filename...${NC}"
        
        # Force update - always copy the file
        cp "$file" "$filename"
        git add "$filename"
        echo -e "${GREEN}  ✅ Updated $filename${NC}"
        CHANGES_MADE=true
    fi
done

# Commit and push changes if any
if [ "$CHANGES_MADE" = true ]; then
    echo ""
    echo -e "${YELLOW}📤 Committing changes to wiki...${NC}"
    
    # Configure git if needed
    if ! git config user.name >/dev/null 2>&1; then
        git config user.name "Wiki Sync Script"
        git config user.email "noreply@github.com"
    fi
    
    # Create commit message with details
    COMMIT_MSG="🔄 Force sync wiki content from repository

Updated from: ${REPO_URL}
Sync method: Manual force sync script
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Files updated:
$(git diff --staged --name-only | sed 's/^/- /')"
    
    git commit -m "$COMMIT_MSG"
    
    if git push origin master; then
        echo -e "${GREEN}🚀 Wiki updated successfully!${NC}"
        
        # List updated files
        echo ""
        echo -e "${BLUE}📄 Updated wiki pages:${NC}"
        git diff HEAD~1 --name-only | while read file; do
            if [ -f "$file" ]; then
                page_name=$(echo "$file" | sed 's/\.md$//' | sed 's/-/ /g')
                echo -e "${GREEN}  - $page_name ($file)${NC}"
            fi
        done
        
        echo ""
        echo -e "${GREEN}🔗 Wiki URL: ${REPO_URL}/wiki${NC}"
        echo -e "${GREEN}✅ Force sync completed successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to push changes to wiki${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}ℹ️ No changes to commit - wiki is already up to date${NC}"
fi

# Cleanup
cd ..
rm -rf "$WIKI_DIR"

echo ""
echo -e "${GREEN}🎉 Wiki force sync completed!${NC}"
echo -e "${BLUE}📖 Visit your wiki at: ${REPO_URL}/wiki${NC}"