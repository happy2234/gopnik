#!/bin/bash

# Enhanced PAT Token Test Script (Supports Classic & Fine-Grained Tokens)
# This script helps verify if your Personal Access Token has the right permissions

set -e

echo "🔍 Testing Personal Access Token..."
echo "=================================="

# Check if PAT_TOKEN is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <PAT_TOKEN>"
    echo "Example: $0 ghp_xxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

PAT_TOKEN="$1"
REPO="happy2234/gopnik"

echo "📋 Testing token permissions for repository: $REPO"
echo ""

# Test 1: Repository access
echo "🔍 Test 1: Repository access..."
if curl -s -H "Authorization: token $PAT_TOKEN" \
   "https://api.github.com/repos/$REPO" | grep -q '"name"'; then
    echo "✅ Repository access: OK"
else
    echo "❌ Repository access: FAILED"
    echo "   Token may not have 'repo' or appropriate fine-grained access"
fi

# Test 2: Push permissions
echo ""
echo "🔍 Test 2: Push permissions..."
if curl -s -H "Authorization: token $PAT_TOKEN" \
   "https://api.github.com/repos/$REPO" | grep -q '"permissions".*"push":true'; then
    echo "✅ Push permissions: OK"
else
    echo "⚠️ Push permission test: WARNING"
    echo "   Cannot reliably determine for fine-grained tokens."
    echo "   Perform an actual git push test instead."
fi

# Test 3: Wiki access
echo ""
echo "🔍 Test 3: Wiki access..."
if curl -s -H "Authorization: token $PAT_TOKEN" \
   "https://api.github.com/repos/$REPO" | grep -q '"has_wiki":true'; then
    echo "✅ Wiki enabled: OK"
else
    echo "⚠️ Wiki access test: WARNING"
    echo "   Wiki may not be enabled or accessible."
fi

# Test 4: Actions permissions
echo ""
echo "🔍 Test 4: Actions permissions..."
if curl -s -H "Authorization: token $PAT_TOKEN" \
   "https://api.github.com/repos/$REPO/actions/workflows" | grep -q '"workflows"'; then
    echo "✅ Actions access: OK"
else
    echo "⚠️ Actions permissions test: WARNING"
    echo "   Cannot reliably detect 'workflow' scope for fine-grained token."
    echo "   Ensure 'Read & Write' is granted in the token settings."
fi

# Test 5: Token scopes (only works reliably for classic PATs)
echo ""
echo "🔍 Test 5: Token scopes..."
SCOPES=$(curl -s -I -H "Authorization: token $PAT_TOKEN" \
         "https://api.github.com/user" | grep -i "x-oauth-scopes" | cut -d: -f2 | tr -d ' \r\n')

if [ -n "$SCOPES" ]; then
    echo "✅ Token scopes (classic PAT): $SCOPES"
    
    if echo "$SCOPES" | grep -q "repo"; then
        echo "  ✅ 'repo' scope: Present"
    else
        echo "  ⚠️ 'repo' scope: Not detected (may be fine-grained token)"
    fi

    if echo "$SCOPES" | grep -q "workflow"; then
        echo "  ✅ 'workflow' scope: Present"
    else
        echo "  ⚠️ 'workflow' scope: Not detected (may be fine-grained token)"
    fi
else
    echo "⚠️ Cannot detect scopes via headers (likely a fine-grained token)"
fi

# Test 6: Repository clone test
echo ""
echo "🔍 Test 6: Repository clone test..."
TEMP_DIR=$(mktemp -d)
if git clone "https://x-access-token:$PAT_TOKEN@github.com/$REPO.git" "$TEMP_DIR/test-repo" 2>/dev/null; then
    echo "✅ Repository clone: OK"
    rm -rf "$TEMP_DIR"
else
    echo "❌ Repository clone: FAILED"
    echo "   Token authentication failed"
    rm -rf "$TEMP_DIR"
fi

# Test 7: Wiki clone test
echo ""
echo "🔍 Test 7: Wiki clone test..."
TEMP_DIR=$(mktemp -d)
if git clone "https://x-access-token:$PAT_TOKEN@github.com/$REPO.wiki.git" "$TEMP_DIR/test-wiki" 2>/dev/null; then
    echo "✅ Wiki clone: OK"
    rm -rf "$TEMP_DIR"
else
    echo "⚠️ Wiki clone test: WARNING"
    echo "   Wiki may not be initialized or accessible"
    rm -rf "$TEMP_DIR"
fi

echo ""
echo "🎯 Summary:"
echo "==========="
echo "- Fine-grained tokens may not show scopes like 'repo' and 'workflow' in headers."
echo "- Best test is actual functionality: clone, push, workflow update."
echo "- If the clone and push tests succeed, your token works."
echo ""
echo "🔗 Create new fine-grained token: https://github.com/settings/tokens"
echo "🔗 Repository secrets: https://github.com/$REPO/settings/secrets/actions"
