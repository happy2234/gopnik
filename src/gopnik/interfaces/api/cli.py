"""
CLI command for running the FastAPI server.
"""

import click
import logging
from .app import run_server


@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--log-level', default='info', help='Log level')
def serve(host: str, port: int, reload: bool, log_level: str):
    """
    Run the Gopnik API server.
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    click.echo(f"Starting Gopnik API server on {host}:{port}")
    if reload:
        click.echo("Auto-reload enabled (development mode)")
    
    try:
        run_server(host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    serve()