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
    
    # Copy static files
    static_src = Path("src/gopnik/interfaces/web/static")
    if static_src.exists():
        static_dest = dist_dir / "static"
        if static_dest.exists():
            shutil.rmtree(static_dest)
        shutil.copytree(static_src, static_dest)
        print("✅ Copied static files")
    
    # Create index.html from welcome template
    template_path = Path("src/gopnik/interfaces/web/templates/welcome.html")
    if template_path.exists():
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Simple template replacement for static deployment
        content = content.replace('{{ title }}', 'Gopnik Web Demo')
        content = content.replace('{{ version }}', '0.1.0')
        content = content.replace('{{ last_updated }}', '2024')
        
        # Add base tag for proper asset loading
        if '<head>' in content:
            content = content.replace('<head>', '<head>\n    <base href="/">')
        
        with open(dist_dir / "index.html", 'w') as f:
            f.write(content)
        print("✅ Created index.html")
    
    # Create demo page
    demo_template = Path("src/gopnik/interfaces/web/templates/demo.html")
    if demo_template.exists():
        with open(demo_template, 'r') as f:
            demo_content = f.read()
        
        # Simple template replacement
        demo_content = demo_content.replace('{{ title }}', 'Gopnik Demo')
        
        with open(dist_dir / "demo.html", 'w') as f:
            f.write(demo_content)
        print("✅ Created demo.html")
    
    # Create _redirects file for SPA routing
    redirects_content = """
# API routes to serverless functions
/api/*  /.netlify/functions/api/:splat  200

# SPA fallback
/*  /index.html  200
"""
    
    with open(dist_dir / "_redirects", 'w') as f:
        f.write(redirects_content.strip())
    print("✅ Created _redirects file")
    
    # Create netlify deployment info
    deploy_info = {
        "name": "gopnik-web-demo",
        "version": "0.1.0",
        "build_time": "2024",
        "features": [
            "Document upload and processing",
            "PII detection and redaction",
            "Multiple redaction profiles",
            "Real-time processing status"
        ]
    }
    
    with open(dist_dir / "deploy-info.json", 'w') as f:
        json.dump(deploy_info, f, indent=2)
    print("✅ Created deployment info")
    
    print("🎉 Build complete! Ready for Netlify deployment.")
    print(f"📁 Files created in: {dist_dir}")
    
    # List created files
    for file in dist_dir.rglob("*"):
        if file.is_file():
            print(f"   - {file.relative_to(dist_dir)}")

if __name__ == "__main__":
    main()