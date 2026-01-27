"""
CiRA FutureEdge Studio - Main Application Entry Point

Copyright 2025 CiRA Team
Licensed under Apache License 2.0
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import after path setup
from ui.main_window import CiRAStudioApp
from core.config import Config
from loguru import logger


def setup_logging():
    """Configure logging system."""
    # Use user's AppData folder for logs (writable without admin)
    if os.name == 'nt':  # Windows
        log_dir = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', PROJECT_ROOT))) / "CiRA FES" / "logs"
    else:  # Linux/Mac
        log_dir = Path.home() / ".cira_fes" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "cira_studio_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    logger.info("CiRA FutureEdge Studio starting...")
    logger.info(f"Logging to: {log_dir}")


def main():
    """Main application entry point."""
    try:
        # Setup logging
        setup_logging()

        # Load configuration
        config = Config.load()
        logger.info(f"Configuration loaded: {config.app_name} v{config.version}")

        # Create and run application
        app = CiRAStudioApp(config)
        logger.info("Application initialized successfully")

        app.run()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
