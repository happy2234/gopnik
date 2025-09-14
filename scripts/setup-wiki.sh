#!/bin/bash

# Script to help set up GitHub Wiki content
# Run this after enabling Wiki in repository settings

echo "🚀 Setting up GitHub Wiki for Gopnik"
echo "======================================"

REPO_URL="https://github.com/happy2234/gopnik"
WIKI_URL="https://github.com/happy2234/gopnik.wiki.git"

echo ""
echo "📋 Manual Steps Required:"
echo "1. Go to: ${REPO_URL}/settings"
echo "2. Enable 'Wikis' in the Features section"
echo "3. Enable 'Discussions' in the Features section"
echo ""

read -p "Have you enabled Wiki and Discussions in GitHub settings? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please enable Wiki and Discussions first, then run this script again."
    exit 1
fi

echo ""
echo "📚 Setting up Wiki content..."

# Check if wiki directory exists
if [ ! -d "wiki" ]; then
    echo "❌ Wiki content directory not found!"
    exit 1
fi

# Clone the wiki repository
echo "📥 Cloning wiki repository..."
if [ -d "temp-wiki" ]; then
    rm -rf temp-wiki
fi

git clone "$WIKI_URL" temp-wiki 2>/dev/null || {
    echo "❌ Could not clone wiki repository. Make sure:"
    echo "   1. Wiki is enabled in repository settings"
    echo "   2. You have write access to the repository"
    echo "   3. You are authenticated with GitHub"
    exit 1
}

cd temp-wiki

# Copy wiki content
echo "📝 Copying wiki content..."
cp ../wiki/*.md .

# Rename files for GitHub Wiki format
if [ -f "Home.md" ]; then
    echo "✅ Home.md ready"
else
    echo "❌ Home.md not found"
fi

if [ -f "Installation-Guide.md" ]; then
    echo "✅ Installation-Guide.md ready"
else
    echo "❌ Installation-Guide.md not found"
fi

# Add and commit wiki content
echo "📤 Uploading wiki content..."
git add .
git config user.name "Gopnik Setup"
git config user.email "setup@gopnik.ai"
git commit -m "Initial wiki setup with installation guide and home page

- Add comprehensive home page with navigation
- Add detailed installation guide for all platforms
- Set up wiki structure for community contributions"

git push origin master

cd ..
rm -rf temp-wiki

echo ""
echo "🎉 Wiki setup complete!"
echo "📖 Visit: ${REPO_URL}/wiki"
echo ""
echo "💬 Discussions should now be available at:"
echo "📖 Visit: ${REPO_URL}/discussions"
echo ""
echo "🔧 Next steps:"
echo "1. Visit the wiki and verify content"
echo "2. Create initial discussion categories"
echo "3. Set up ReadTheDocs integration"
echo ""