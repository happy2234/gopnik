#!/usr/bin/env python3
"""
Build script for Netlify deployment.
"""

import os
import shutil
from pathlib import Path
import json

def main():
    """Build the Netlify deployment."""
    print("🚀 Building Gopnik web demo for Netlify...")
    
    # Create dist directory
    dist_dir = Path("netlify/dist")
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy static files if they exist
    static_src = Path("src/gopnik/interfaces/web/static")
    if static_src.exists():
        static_dest = dist_dir / "static"
        if static_dest.exists():
            shutil.rmtree(static_dest)
        shutil.copytree(static_src, static_dest)
        print("✅ Copied static files")
    else:
        # Create basic static structure
        (dist_dir / "static" / "css").mkdir(parents=True, exist_ok=True)
        (dist_dir / "static" / "js").mkdir(parents=True, exist_ok=True)
        print("✅ Created static directories")
    
    # Create index.html
    index_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gopnik Web Demo</title>
    <base href="/">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .feature { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Gopnik Web Demo</h1>
        <p>AI-powered document deidentification toolkit</p>
        
        <div class="feature">
            <h3>🚀 Quick Start</h3>
            <p>Install Gopnik and start processing documents:</p>
            <code>pip install gopnik</code>
        </div>
        
        <div class="feature">
            <h3>🌐 API Demo</h3>
            <p>Try the API endpoints:</p>
            <a href="/api/health" class="btn">Health Check</a>
            <a href="/api/docs" class="btn">API Documentation</a>
        </div>
        
        <div class="feature">
            <h3>📖 Documentation</h3>
            <p>Learn more about Gopnik:</p>
            <a href="https://happy2234.github.io/gopnik/" class="btn">Documentation</a>
            <a href="https://github.com/happy2234/gopnik" class="btn">GitHub</a>
        </div>
        
        <div class="feature">
            <h3>✨ Features</h3>
            <ul>
                <li>AI-powered PII detection</li>
                <li>Multiple document formats</li>
                <li>Batch processing</li>
                <li>Audit trails</li>
                <li>Profile management</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    with open(dist_dir / "index.html", 'w') as f:
        f.write(index_content)
    print("✅ Created index.html")
    
    # Create _redirects file for SPA routing
    redirects_content = """# API routes to serverless functions
/api/*  /.netlify/functions/api/:splat  200

# SPA fallback
/*  /index.html  200"""
    
    with open(dist_dir / "_redirects", 'w') as f:
        f.write(redirects_content)
    print("✅ Created _redirects file")
    
    # Create netlify deployment info
    deploy_info = {
        "name": "gopnik-web-demo",
        "version": "0.1.0",
        "build_time": "2024",
        "status": "active"
    }
    
    with open(dist_dir / "deploy-info.json", 'w') as f:
        json.dump(deploy_info, f, indent=2)
    print("✅ Created deployment info")
    
    print("🎉 Build complete! Ready for Netlify deployment.")
    print(f"📁 Files created in: {dist_dir}")
    
    # List created files
    try:
        for file in dist_dir.rglob("*"):
            if file.is_file():
                print(f"   - {file.relative_to(dist_dir)}")
    except Exception as e:
        print(f"   - Could not list files: {e}")

if __name__ == "__main__":
    main()