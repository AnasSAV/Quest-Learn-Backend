#!/usr/bin/env python3

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Testing database connection to: {DATABASE_URL}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"✅ Database connection successful! Test query result: {row}")
        
        # Test a more detailed query
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Additional diagnostic info
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
