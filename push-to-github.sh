#!/bin/bash
# GitHub Push Helper for ffmpeg-scripts

echo "=== GitHub Repository Setup for ffmpeg-scripts ==="
echo ""
echo "📋 Step 1: Create a new repository on GitHub"
echo "   1. Go to: https://github.com/new"
echo "   2. Repository name: ffmpeg-scripts"
echo "   3. Description: A comprehensive collection of 50+ FFmpeg-based scripts"
echo "   4. Make it PUBLIC (or private if you prefer)"
echo "   5. DON'T initialize with README (we already have one)"
echo "   6. Click 'Create repository'"
echo ""
echo "📋 Step 2: After creating, GitHub will show you commands."
echo "   Copy your repository URL (looks like: https://github.com/YOUR_USERNAME/ffmpeg-scripts.git)"
echo ""
read -p "👉 Enter your GitHub repository URL: " REPO_URL

if [[ -z "$REPO_URL" ]]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

cd /home/mik/ffmpeg-scripts

echo ""
echo "🔧 Setting up remote..."
git remote add origin "$REPO_URL"

echo "🔧 Renaming branch to main..."
git branch -M main

echo "📤 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Your repository should now be live at:"
echo "   ${REPO_URL%.git}"
echo ""
echo "📊 Repository stats:"
echo "   - 52 scripts total"
echo "   - 5 motion vector scripts"
echo "   - 47 ASCII art scripts"
echo ""
echo "🌟 Don't forget to:"
echo "   1. Add a star to your own repo!"
echo "   2. Update README.md with your GitHub username"
echo "   3. Add topics: ffmpeg, video-processing, ascii-art, motion-vectors"
