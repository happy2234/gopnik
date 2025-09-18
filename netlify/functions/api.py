"""
Netlify serverless function for Gopnik web demo.
"""

import json
import os
from pathlib import Path
import sys

def handler(event, context):
    """
    Simple API handler for Netlify deployment.
    """
    try:
        # Add the src directory to Python path
        current_dir = Path(__file__).parent
        src_dir = current_dir.parent.parent / "src"
        sys.path.insert(0, str(src_dir))
        
        # Try to import and create the app
        from gopnik.interfaces.web.routes import create_demo_app
        from mangum import Mangum
        
        # Create FastAPI app
        app = create_demo_app()
        
        # Create Mangum handler for serverless deployment
        mangum_handler = Mangum(app, lifespan="off")
        
        # Call the handler
        return mangum_handler(event, context)
        
    except ImportError as e:
        # Fallback response if imports fail
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
            },
            "body": json.dumps({
                "message": "Gopnik Web Demo API",
                "status": "limited_functionality",
                "error": str(e),
                "note": "This is a demo deployment. Full functionality requires local installation.",
                "install": "pip install gopnik",
                "docs": "https://happy2234.github.io/gopnik/"
            })
        }
    except Exception as e:
        # General error handler
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Server error",
                "message": str(e)
            })
        }