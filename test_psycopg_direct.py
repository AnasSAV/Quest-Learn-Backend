#!/usr/bin/env python3

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Convert SQLAlchemy URL to psycopg URL
PSYCOPG_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
print(f"Testing direct psycopg connection...")
print(f"Original Database URL: {DATABASE_URL}")
print(f"Psycopg Database URL: {PSYCOPG_URL}")

# Parse the URL manually to understand the components
from urllib.parse import urlparse

parsed = urlparse(PSYCOPG_URL)
print(f"Host: {parsed.hostname}")
print(f"Port: {parsed.port}")
print(f"Database: {parsed.path[1:]}")  # Remove leading /
print(f"Username: {parsed.username}")

try:
    # Try direct psycopg connection
    conn = psycopg.connect(PSYCOPG_URL)
    print("✅ Direct psycopg connection successful!")
    
    with conn.cursor() as cur:
        cur.execute("SELECT 1 as test")
        result = cur.fetchone()
        print(f"✅ Test query result: {result}")
        
    conn.close()
    
except Exception as e:
    print(f"❌ Direct psycopg connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to diagnose further
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to test hostname resolution more directly
    print(f"\nTrying to resolve hostname: {parsed.hostname}")
    try:
        import socket
        ip = socket.gethostbyname(parsed.hostname)
        print(f"✅ Hostname resolved to: {ip}")
    except Exception as resolve_e:
        print(f"❌ Hostname resolution failed: {resolve_e}")
