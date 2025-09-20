#!/usr/bin/env python3
"""
Simplified build script for Netlify deployment.
This version doesn't require the full Gopnik dependencies.
"""

import os
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime

def main():
    """Build the Netlify deployment with minimal dependencies."""
    parser = argparse.ArgumentParser(description="Build Gopnik for Netlify deployment")
    parser.add_argument("--production", action="store_true", help="Production build")
    parser.add_argument("--preview", action="store_true", help="Preview build")
    parser.add_argument("--branch", action="store_true", help="Branch build")
    
    args = parser.parse_args()
    
    print("🚀 Building Gopnik web demo for Netlify (simplified)...")
    print(f"   Mode: {'Production' if args.production else 'Development'}")
    
    # Create dist directory
    dist_dir = Path("netlify/dist")
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Create static directories
    (dist_dir / "static" / "css").mkdir(parents=True, exist_ok=True)
    (dist_dir / "static" / "js").mkdir(parents=True, exist_ok=True)
    print("✅ Created static directories")
    
    # Create enhanced CSS
    create_enhanced_css(dist_dir)
    
    # Create index.html
    create_index_html(dist_dir, args)
    
    # Create _redirects file
    create_redirects(dist_dir)
    
    # Create deployment info
    create_deployment_info(dist_dir, args)
    
    print("🎉 Build complete! Ready for Netlify deployment.")
    print(f"📁 Files created in: {dist_dir}")
    
    # List created files
    try:
        for file in dist_dir.rglob("*"):
            if file.is_file():
                print(f"   - {file.relative_to(dist_dir)}")
    except Exception as e:
        print(f"   - Could not list files: {e}")


def create_enhanced_css(dist_dir):
    """Create enhanced CSS file."""
    css_content = '''/* Enhanced Gopnik Demo Styles */
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


def create_index_html(dist_dir, args):
    """Create the main index.html file."""
    mode_text = "Production" if args.production else "Development"
    
    index_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gopnik - AI-Powered Deidentification Toolkit</title>
    <base href="/">
    <link rel="stylesheet" href="/static/css/enhanced.css">
    <meta name="description" content="AI-powered forensic-grade deidentification toolkit for document PII redaction">
    <meta name="keywords" content="PII, deidentification, redaction, privacy, AI, forensic, document processing">
    <meta name="author" content="Gopnik Development Team">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://gopnik.netlify.app/">
    <meta property="og:title" content="Gopnik - AI-Powered Deidentification Toolkit">
    <meta property="og:description" content="AI-powered forensic-grade deidentification toolkit for document PII redaction">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://gopnik.netlify.app/">
    <meta property="twitter:title" content="Gopnik - AI-Powered Deidentification Toolkit">
    <meta property="twitter:description" content="AI-powered forensic-grade deidentification toolkit for document PII redaction">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Gopnik</h1>
            <p>AI-Powered Forensic-Grade Document Deidentification</p>
            <small>Build Mode: {mode_text}</small>
        </div>
        
        <div class="card">
            <h3>🚀 Quick Start</h3>
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
        
        <div class="card">
            <h3>🌐 API Endpoints</h3>
            <p>RESTful API for programmatic integration and automation.</p>
            <div class="install-code">
# Health check<br>
curl https://your-api.com/api/v1/health<br><br>
# Process document<br>
curl -X POST https://your-api.com/api/v1/process \\<br>
  -F "file=@document.pdf" \\<br>
  -F "profile_name=healthcare"
            </div>
        </div>
        
        <div class="footer">
            <p>Built with ❤️ for privacy and security • Open Source MIT License</p>
            <p>Deploy your own: <a href="https://app.netlify.com/start/deploy?repository=https://github.com/happy2234/gopnik">Deploy to Netlify</a></p>
        </div>
    </div>
</body>
</html>'''
    
    with open(dist_dir / "index.html", 'w') as f:
        f.write(index_content)
    
    print("✅ Created index.html")


def create_redirects(dist_dir):
    """Create _redirects file for Netlify."""
    redirects_content = """# Redirect API calls to documentation for now
/api/* https://happy2234.github.io/gopnik/user-guide/api/ 302

# SPA fallback
/* /index.html 200"""
    
    with open(dist_dir / "_redirects", 'w') as f:
        f.write(redirects_content)
    
    print("✅ Created _redirects file")


def create_deployment_info(dist_dir, args):
    """Create deployment info file."""
    deploy_info = {
        "name": "gopnik-web-demo",
        "version": "0.1.0",
        "type": "static-site",
        "build_time": datetime.now().isoformat(),
        "mode": "production" if args.production else "development",
        "status": "active",
        "features": [
            "responsive_design",
            "enhanced_styling",
            "performance_optimized",
            "security_headers",
            "seo_friendly"
        ]
    }
    
    with open(dist_dir / "deploy-info.json", 'w') as f:
        json.dump(deploy_info, f, indent=2)
    
    print("✅ Created deployment info")


if __name__ == "__main__":
    main()
