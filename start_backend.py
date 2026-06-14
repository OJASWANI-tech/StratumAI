#!/usr/bin/env python3
"""
Startup script for the Viz.AI FastAPI backend
"""

import os
import sys
import uvicorn
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pandas
        import numpy
        import groq
        import dotenv
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    return True

def check_environment():
    """Check if environment variables are set"""
    env_file = Path(".env.local")
    if not env_file.exists():
        print("⚠️  .env.local file not found")
        print("Please create .env.local with your GROQ_API_KEY")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in .env.local")
        print("Please add: GROQ_API_KEY=your_api_key_here")
        return False
    
    print("✅ Environment variables configured")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "generated_dashboards"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main startup function"""
    print("🚀 Starting Viz.AI Backend...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n🎉 Backend ready to start!")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the FastAPI server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 