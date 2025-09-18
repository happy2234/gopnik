"""
Netlify serverless function for Gopnik web demo.
"""

import json
import os
from pathlib import Path
import sys

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from gopnik.interfaces.web.routes import create_demo_app
    from mangum import Mangum
    
    # Create FastAPI app
    app = create_demo_app()
    
    # Create Mangum handler for serverless deployment
    handler = Mangum(app, lifespan="off")
    
except ImportError as e:
    # Fallback handler if imports fail
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Import error",
                "message": str(e),
                "note": "This is a demo deployment. Some features may be limited."
            })
        }