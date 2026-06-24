#!/usr/bin/env python3
"""
Medical AI Engine - Main entry point
"""
import sys
import os
import argparse
import logging

from src.api.server import run_server
from src.cli.extractor import MedicalQuestionExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Medical AI Engine - Extract medical questions from PDFs and images"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start FastAPI server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract questions from file")
    extract_parser.add_argument("--input", "-i", required=True, help="Input file")
    extract_parser.add_argument("--output", "-o", help="Output JSON file")
    extract_parser.add_argument("--type", "-t", choices=["pdf", "image", "text"], help="File type")
    extract_parser.add_argument("--save-db", action="store_true", help="Save to database")
    extract_parser.add_argument("--batch", action="store_true", help="Batch mode")
    extract_parser.add_argument("--pattern", "-p", default="*.pdf", help="File pattern")
    
    args = parser.parse_args()
    
    # Default to server if no command specified
    if not args.command:
        args.command = "server"
        args.host = "0.0.0.0"
        args.port = int(os.environ.get("PORT", 8000))
        args.no_reload = True
    
    try:
        if args.command == "server":
            run_server(
                host=args.host,
                port=args.port,
                reload=not args.no_reload
            )
        
        elif args.command == "extract":
            extractor = MedicalQuestionExtractor()
            
            if args.batch:
                success = extractor.process_directory(
                    args.input,
                    args.output,
                    args.save_db,
                    args.pattern
                )
            else:
                success = extractor.process_file(
                    args.input,
                    args.output,
                    args.save_db,
                    args.type
                )
            
            return 0 if success else 1
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
