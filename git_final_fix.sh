#!/bin/bash

echo "🔧 Final crypto message fix..."

# Add and commit changes
git add public_menu.py
git commit -m "🔧 Final fix: Remove duplicate function and clean code - complete crypto message formatter"

# Push to GitHub
git push origin main

echo "✅ Fix completed!"