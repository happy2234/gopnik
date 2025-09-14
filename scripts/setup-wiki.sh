#!/bin/bash

# Enhanced script to set up GitHub Wiki content
# Can be run locally or used as reference for manual setup

echo "🚀 Setting up GitHub Wiki for Gopnik"
echo "======================================"

REPO_URL="https://github.com/happy2234/gopnik"
WIKI_URL="https://github.com/happy2234/gopnik.wiki.git"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup wiki via GitHub Actions (recommended)
setup_via_actions() {
    echo ""
    echo "🤖 Automated Setup via GitHub Actions (Recommended)"
    echo "=================================================="
    echo ""
    echo "1. Enable Wiki in repository settings:"
    echo "   - Go to: ${REPO_URL}/settings"
    echo "   - Scroll to 'Features' section"
    echo "   - Check ☑️ 'Wikis'"
    echo "   - Save changes"
    echo ""
    echo "2. Trigger the automated setup:"
    echo "   - Go to: ${REPO_URL}/actions"
    echo "   - Find 'Setup GitHub Wiki' workflow"
    echo "   - Click 'Run workflow'"
    echo "   - Wait for completion"
    echo ""
    echo "3. Verify setup:"
    echo "   - Visit: ${REPO_URL}/wiki"
    echo "   - Check that all pages are available"
    echo ""
    echo "✨ The GitHub Actions workflow will:"
    echo "   - Automatically copy all wiki content"
    echo "   - Set up proper page structure"
    echo "   - Enable auto-sync for future updates"
    echo "   - Create status tracking"
    echo ""
}

# Function to setup wiki manually
setup_manually() {
    echo ""
    echo "📋 Manual Setup Process"
    echo "======================"
    echo ""
    
    read -p "Have you enabled Wiki in GitHub repository settings? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Please enable Wiki first:"
        echo "   1. Go to: ${REPO_URL}/settings"
        echo "   2. Enable 'Wikis' in the Features section"
        echo "   3. Save changes"
        echo "   4. Run this script again"
        exit 1
    fi

    echo "📚 Setting up Wiki content..."

    # Check if wiki directory exists
    if [ ! -d "wiki" ]; then
        echo "❌ Wiki content directory not found!"
        echo "   Make sure you're running this from the repository root"
        exit 1
    fi

    # Clone the wiki repository
    echo "📥 Cloning wiki repository..."
    if [ -d "temp-wiki" ]; then
        rm -rf temp-wiki
    fi

    git clone "$WIKI_URL" temp-wiki 2>/dev/null || {
        echo "❌ Could not clone wiki repository. This might mean:"
        echo "   1. Wiki is not enabled in repository settings"
        echo "   2. You don't have write access to the repository"
        echo "   3. You are not authenticated with GitHub"
        echo ""
        echo "💡 Try the automated setup instead (option 1)"
        exit 1
    }

    cd temp-wiki

    # Copy wiki content
    echo "📝 Copying wiki content..."
    
    # Copy all markdown files from wiki directory
    for file in ../wiki/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            cp "$file" "$filename"
            echo "   ✅ Copied $filename"
        fi
    done

    # Verify essential files
    essential_files=("Home.md" "Installation-Guide.md" "Data-Models-Guide.md")
    for file in "${essential_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file ready"
        else
            echo "   ⚠️  $file not found (will be created)"
        fi
    done

    # Create Home.md if it doesn't exist
    if [ ! -f "Home.md" ]; then
        echo "📄 Creating Home.md..."
        cat > Home.md << 'EOF'
# Gopnik Wiki

Welcome to the Gopnik community wiki! This is a collaborative space where users and developers can share knowledge, examples, and best practices.

## 📚 Available Pages

- [Installation Guide](Installation-Guide): Step-by-step installation instructions
- [Data Models Guide](Data-Models-Guide): Complete guide to Gopnik's data structures
- [AI Training Guide](AI-Training-Guide): Comprehensive AI model training procedures

## 🤝 Contributing

This wiki is maintained by the community. Anyone can contribute by editing pages and adding examples.

## 📞 Getting Help

- [GitHub Discussions](https://github.com/happy2234/gopnik/discussions): Ask questions and get help
- [Issue Tracker](https://github.com/happy2234/gopnik/issues): Report bugs and request features
- [Documentation](https://happy2234.github.io/gopnik/): Official documentation
EOF
    fi

    # Add and commit wiki content
    echo "📤 Uploading wiki content..."
    git add .
    
    # Configure git if needed
    if ! git config user.name >/dev/null 2>&1; then
        git config user.name "Gopnik Setup"
        git config user.email "setup@gopnik.ai"
    fi
    
    # Check if there are changes to commit
    if git diff --staged --quiet; then
        echo "ℹ️  No changes to commit (wiki already up to date)"
    else
        git commit -m "📚 Initial wiki setup with comprehensive content

- Add comprehensive home page with navigation
- Add detailed installation guide for all platforms
- Add data models guide with examples
- Add AI training guide with SignVeRod dataset info
- Set up wiki structure for community contributions

Auto-generated by setup script"

        git push origin master || {
            echo "❌ Failed to push to wiki repository"
            echo "   This might be due to permissions or network issues"
            exit 1
        }
    fi

    cd ..
    rm -rf temp-wiki

    echo ""
    echo "🎉 Manual wiki setup complete!"
}

# Function to show status and next steps
show_completion() {
    echo ""
    echo "🎉 Wiki Setup Complete!"
    echo "======================"
    echo ""
    echo "📖 Your wiki is now available at:"
    echo "   ${REPO_URL}/wiki"
    echo ""
    echo "📝 Available pages:"
    echo "   - Home: Main wiki landing page"
    echo "   - Installation Guide: Platform-specific installation"
    echo "   - Data Models Guide: Complete data structure reference"
    echo "   - AI Training Guide: Model training with SignVeRod dataset"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Visit the wiki and verify all content"
    echo "   2. Enable Discussions in repository settings"
    echo "   3. Set up GitHub Pages for documentation"
    echo "   4. Configure automated workflows"
    echo ""
    echo "💡 Pro tip: Use the GitHub Actions workflow for automatic updates!"
}

# Main menu
echo ""
echo "Choose setup method:"
echo "1. 🤖 Automated setup via GitHub Actions (Recommended)"
echo "2. 📋 Manual setup via this script"
echo "3. ❓ Show help and exit"
echo ""

read -p "Enter your choice (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        setup_via_actions
        ;;
    2)
        setup_manually
        show_completion
        ;;
    3)
        echo ""
        echo "📖 Help Information"
        echo "=================="
        echo ""
        echo "This script helps set up the GitHub Wiki for Gopnik with all"
        echo "the prepared content including installation guides, data model"
        echo "documentation, and AI training procedures."
        echo ""
        echo "🤖 Automated Setup (Option 1):"
        echo "   - Uses GitHub Actions workflow"
        echo "   - Handles all setup automatically"
        echo "   - Enables auto-sync for future updates"
        echo "   - Recommended for most users"
        echo ""
        echo "📋 Manual Setup (Option 2):"
        echo "   - Runs setup locally via git commands"
        echo "   - Requires git authentication"
        echo "   - Good for troubleshooting or custom setups"
        echo ""
        echo "For more information, see:"
        echo "   - SETUP_CHECKLIST.md"
        echo "   - .github/workflows/setup-wiki.yml"
        echo ""
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac