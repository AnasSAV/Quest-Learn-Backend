#!/usr/bin/env python3
"""
Startup script for Math Buddy Backend.
This script handles database initialization and starts the FastAPI server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.init_db import init_db, create_demo_data
from app.core.config import settings


async def initialize_database():
    """Initialize the database and optionally create demo data."""
    print("🔧 Initializing database...")
    await init_db()
    print("✅ Database tables created successfully!")
    
    if settings.APP_ENV == "dev":
        print("🎯 Creating demo data for development...")
        await create_demo_data()
        print("✅ Demo data created successfully!")


async def main():
    """Main startup function."""
    print("🚀 Starting Math Buddy Backend...")
    print(f"📝 Environment: {settings.APP_ENV}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Local'}")
    
    try:
        await initialize_database()
        print("🎉 Backend initialized successfully!")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--init-only":
            print("🔧 Database initialization complete. Exiting...")
            return
        
        print("🌐 Starting FastAPI server...")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("🔧 To stop the server, press Ctrl+C")
        print("-" * 50)
        
        # Start the server
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.APP_ENV == "dev",
            log_level="info" if settings.APP_ENV == "dev" else "warning"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Math Buddy Backend...")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
