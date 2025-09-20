#!/bin/bash
# Deploy Gopnik to Netlify

set -e

echo "🚀 Deploying Gopnik to Netlify..."

# Check if Netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "❌ Netlify CLI not found. Installing..."
    npm install -g netlify-cli
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run from the project root."
    exit 1
fi

# Build the project
echo "📦 Building project..."
python scripts/build-netlify.py --production --minify

# Check if build was successful
if [ ! -d "netlify/dist" ]; then
    echo "❌ Build failed. No dist directory found."
    exit 1
fi

echo "✅ Build completed successfully"

# Deploy to Netlify
echo "🌐 Deploying to Netlify..."

# Check if already logged in
if ! netlify status &> /dev/null; then
    echo "🔐 Please log in to Netlify..."
    netlify login
fi

# Deploy
if [ "$1" = "--prod" ]; then
    echo "🚀 Deploying to production..."
    netlify deploy --prod --dir=netlify/dist
else
    echo "🧪 Deploying preview..."
    netlify deploy --dir=netlify/dist
fi

echo "🎉 Deployment completed!"
echo "📱 Check your Netlify dashboard for the deployment URL"
