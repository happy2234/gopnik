#!/usr/bin/env python3
"""
Enhanced build script for Netlify deployment.
Supports static site, serverless functions, and multiple deployment modes.
"""

import os
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import sys

def main():
    """Build the Netlify deployment with enhanced features."""
    parser = argparse.ArgumentParser(description="Build Gopnik for Netlify deployment")
    parser.add_argument("--production", action="store_true", help="Production build")
    parser.add_argument("--preview", action="store_true", help="Preview build")
    parser.add_argument("--branch", action="store_true", help="Branch build")
    parser.add_argument("--with-functions", action="store_true", help="Include serverless functions")
    parser.add_argument("--minify", action="store_true", help="Minify assets")
    
    args = parser.parse_args()
    
    print("🚀 Building Gopnik web demo for Netlify...")
    print(f"   Mode: {'Production' if args.production else 'Development'}")
    print(f"   Functions: {'Yes' if args.with_functions else 'No'}")
    print(f"   Minify: {'Yes' if args.minify else 'No'}")
    
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
    
    # Create serverless functions if requested
    if args.with_functions:
        create_serverless_functions()
    
    # Copy additional assets
    copy_additional_assets(dist_dir, args)
    
    # Create index.html
    index_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gopnik - AI-Powered Deidentification Toolkit</title>
    <base href="/">
    <link rel="stylesheet" href="/static/css/enhanced.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .card { background: white; border-radius: 15px; padding: 30px; margin: 20px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: #667eea; margin-bottom: 15px; font-size: 1.5rem; }
        .btn { display: inline-block; padding: 12px 24px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; text-decoration: none; border-radius: 25px; margin: 10px 10px 10px 0; transition: all 0.3s ease; font-weight: 500; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 40px 0; }
        .feature-item { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; color: white; }
        .feature-item h4 { margin-bottom: 10px; color: #fff; }
        .install-code { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; margin: 15px 0; }
        .footer { text-align: center; color: rgba(255,255,255,0.8); margin-top: 60px; }
        @media (max-width: 768px) { .header h1 { font-size: 2rem; } .container { padding: 15px; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Gopnik</h1>
            <p>AI-Powered Forensic-Grade Document Deidentification</p>
        </div>
        
        <div class="card">
            <h3>� Quiuck Start</h3>
            <p>Get started with Gopnik in seconds. Install via pip and start processing documents immediately.</p>
            <div class="install-code">pip install gopnik</div>
            <div class="install-code">gopnik process document.pdf --profile healthcare</div>
        </div>
        
        <div class="features">
            <div class="feature-item">
                <h4>🤖 AI-Powered Detection</h4>
                <p>Advanced computer vision and NLP for comprehensive PII detection</p>
            </div>
            <div class="feature-item">
                <h4>📄 Multiple Formats</h4>
                <p>Support for PDF, images, and complex document layouts</p>
            </div>
            <div class="feature-item">
                <h4>⚡ Batch Processing</h4>
                <p>Process thousands of documents with progress tracking</p>
            </div>
            <div class="feature-item">
                <h4>🔐 Forensic Grade</h4>
                <p>Cryptographic audit trails and integrity validation</p>
            </div>
        </div>
        
        <div class="card">
            <h3>📖 Documentation & Resources</h3>
            <p>Everything you need to get started with Gopnik deidentification.</p>
            <a href="https://happy2234.github.io/gopnik/" class="btn">📚 Documentation</a>
            <a href="https://github.com/happy2234/gopnik" class="btn">💻 GitHub</a>
            <a href="https://github.com/happy2234/gopnik/discussions" class="btn">💬 Discussions</a>
            <a href="https://pypi.org/project/gopnik/" class="btn">📦 PyPI</a>
        </div>
        
        <div class="card">
            <h3>🛠️ CLI Commands</h3>
            <p>Powerful command-line interface for all your deidentification needs.</p>
            <div class="install-code">
# Process a single document<br>
gopnik process document.pdf --profile healthcare<br><br>
# Batch process a directory<br>
gopnik batch /documents --profile default --recursive<br><br>
# Validate document integrity<br>
gopnik validate document.pdf --audit-dir /logs<br><br>
# Manage profiles<br>
gopnik profile list --verbose
            </div>
        </div>
        
        <div class="footer">
            <p>Built with ❤️ for privacy and security • Open Source MIT License</p>
            <p>Deploy your own: <a href="https://app.netlify.com/start/deploy?repository=https://github.com/happy2234/gopnik" style="color: #fff;">Deploy to Netlify</a></p>
        </div>
    </div>
</body>
</html>"""
    
    with open(dist_dir / "index.html", 'w') as f:
        f.write(index_content)
    print("✅ Created index.html")
    
    # Create _redirects file (simplified)
    redirects_content = """# Redirect API calls to documentation for now
/api/* https://happy2234.github.io/gopnik/user-guide/api/ 302

# SPA fallback
/* /index.html 200"""
    
    with open(dist_dir / "_redirects", 'w') as f:
        f.write(redirects_content)
    print("✅ Created _redirects file")
    
    # Create deployment info
    deploy_info = {
        "name": "gopnik-web-demo",
        "version": "0.1.0",
        "type": "static-site",
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


def create_serverless_functions():
    """Create serverless functions for API endpoints."""
    functions_dir = Path("netlify/functions")
    functions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create API function
    api_function = functions_dir / "api.py"
    api_content = '''import json
from http.server import BaseHTTPRequestHandler
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Gopnik API - Static Demo Mode",
            "status": "active",
            "note": "This is a static demo. For full functionality, use the CLI or local API server.",
            "endpoints": {
                "health": "/api/health",
                "docs": "https://happy2234.github.io/gopnik/",
                "github": "https://github.com/happy2234/gopnik"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        self.send_response(501)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "error": "Not implemented in static demo",
            "message": "Use the CLI tool or local API server for full functionality"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
'''
    
    with open(api_function, 'w') as f:
        f.write(api_content)
    
    print("✅ Created serverless functions")


def copy_additional_assets(dist_dir, args):
    """Copy additional assets and create enhanced content."""
    # Create enhanced CSS
    css_content = '''
/* Enhanced Gopnik Demo Styles */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #f093fb;
    --text-color: #333;
    --bg-gradient: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background: var(--bg-gradient);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    color: white;
    margin-bottom: 40px;
}

.header h1 {
    font-size: 3.5rem;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    background: linear-gradient(45deg, #fff, #f0f0f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header p {
    font-size: 1.3rem;
    opacity: 0.9;
    margin-bottom: 20px;
}

.card {
    background: white;
    border-radius: 20px;
    padding: 40px;
    margin: 30px 0;
    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border: 1px solid rgba(255,255,255,0.2);
}

.card:hover {
    transform: translateY(-8px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
}

.card h3 {
    color: var(--primary-color);
    margin-bottom: 20px;
    font-size: 1.8rem;
    font-weight: 600;
}

.btn {
    display: inline-block;
    padding: 15px 30px;
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
    color: white;
    text-decoration: none;
    border-radius: 30px;
    margin: 10px 15px 10px 0;
    transition: all 0.3s ease;
    font-weight: 600;
    font-size: 1rem;
    border: none;
    cursor: pointer;
}

.btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    text-decoration: none;
    color: white;
}

.btn-secondary {
    background: linear-gradient(45deg, #6c757d, #495057);
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
    margin: 50px 0;
}

.feature-item {
    background: rgba(255,255,255,0.15);
    padding: 25px;
    border-radius: 15px;
    color: white;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    transition: all 0.3s ease;
}

.feature-item:hover {
    background: rgba(255,255,255,0.25);
    transform: translateY(-5px);
}

.feature-item h4 {
    margin-bottom: 15px;
    color: #fff;
    font-size: 1.3rem;
}

.install-code {
    background: #1a1a1a;
    color: #e2e8f0;
    padding: 20px;
    border-radius: 10px;
    font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
    margin: 20px 0;
    border-left: 4px solid var(--primary-color);
    overflow-x: auto;
}

.footer {
    text-align: center;
    color: rgba(255,255,255,0.8);
    margin-top: 80px;
    padding: 40px 0;
}

.footer a {
    color: #fff;
    text-decoration: none;
    font-weight: 600;
}

.footer a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .header h1 { font-size: 2.5rem; }
    .container { padding: 15px; }
    .card { padding: 25px; }
    .btn { padding: 12px 24px; margin: 8px 10px 8px 0; }
}

/* Animation for loading */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.card {
    animation: fadeInUp 0.6s ease-out;
}

.card:nth-child(2) { animation-delay: 0.1s; }
.card:nth-child(3) { animation-delay: 0.2s; }
.card:nth-child(4) { animation-delay: 0.3s; }
'''
    
    css_file = dist_dir / "static" / "css" / "enhanced.css"
    with open(css_file, 'w') as f:
        f.write(css_content)
    
    print("✅ Created enhanced CSS")

if __name__ == "__main__":
    main()