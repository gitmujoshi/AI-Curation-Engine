#!/bin/bash
set -e

# Script to push Perimeter to its own repository
# Run this on a computer with Git and terminal access

echo "🚀 Pushing Perimeter to New Repository"
echo "======================================="
echo ""

# Check if we're in the right directory
if [ ! -d "src" ] || [ ! -d "saas" ]; then
    echo "❌ Error: Please run this script from the repository root"
    echo "   This directory should contain: src/, saas/, infra/, etc."
    exit 1
fi

echo "✅ Found Perimeter files"
echo ""

# Create temporary directory for new repo
TEMP_DIR=$(mktemp -d)
echo "📁 Creating temporary directory: $TEMP_DIR"

# Copy all Perimeter files
echo "📦 Copying files..."
cp -r src "$TEMP_DIR/"
cp -r saas "$TEMP_DIR/"
cp -r infra "$TEMP_DIR/"
cp -r tests "$TEMP_DIR/"
cp -r docs "$TEMP_DIR/"
cp -r examples "$TEMP_DIR/"
cp -r config "$TEMP_DIR/"
cp -r scripts "$TEMP_DIR/"
cp README.md "$TEMP_DIR/"
cp LICENSE "$TEMP_DIR/"
cp CONTRIBUTING.md "$TEMP_DIR/"
cp DEPLOYMENT.md "$TEMP_DIR/"
cp DEPLOYMENT_SUMMARY.md "$TEMP_DIR/"
cp E2E_TEST_REPORT.md "$TEMP_DIR/"
cp FINAL_STATUS.md "$TEMP_DIR/"
cp TEST_RESULTS_SUMMARY.md "$TEMP_DIR/"
cp REPOSITORY_STRUCTURE.md "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp pyproject.toml "$TEMP_DIR/"
cp Dockerfile "$TEMP_DIR/"
cp .dockerignore "$TEMP_DIR/" 2>/dev/null || true
cp docker-compose.yml "$TEMP_DIR/"
cp .gitignore "$TEMP_DIR/"

echo "✅ Files copied"
echo ""

# Initialize new repo
cd "$TEMP_DIR"
git init
git add -A
git commit -m "feat: initial Perimeter AI Security Gateway repository

Complete enterprise-grade AI security gateway implementation"

echo "✅ Git repository initialized"
echo ""

# Add remote and push
echo "🔗 Adding remote..."
git remote add origin https://github.com/gitmujoshi/perimeter-gateway.git
git branch -M main

echo "📤 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ SUCCESS! Perimeter has been pushed to:"
echo "   https://github.com/gitmujoshi/perimeter-gateway"
echo ""
echo "🧹 Cleaning up temporary directory..."
cd -
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 Done!"
