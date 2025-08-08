#!/usr/bin/env python3

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Convert SQLAlchemy URL to psycopg URL
PSYCOPG_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

print(f"Testing various connection methods...")

# Try 1: Original hostname
print(f"\n1. Testing with original hostname:")
print(f"URL: {PSYCOPG_URL}")

try:
    conn = psycopg.connect(PSYCOPG_URL)
    print("✅ Connection with hostname successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection with hostname failed: {e}")

# Try 2: Using IP address directly
print(f"\n2. Testing with IP address (172.64.149.246):")
IP_URL = PSYCOPG_URL.replace("sjbwnjqunhonucocaoiu.supabase.co", "172.64.149.246")
print(f"URL: {IP_URL}")

try:
    conn = psycopg.connect(IP_URL)
    print("✅ Connection with IP successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection with IP failed: {e}")

# Try 3: Using connection parameters explicitly with SSL
print(f"\n3. Testing with explicit SSL parameters:")
SSL_URL = PSYCOPG_URL + "?sslmode=require"
print(f"URL: {SSL_URL}")

try:
    conn = psycopg.connect(SSL_URL)
    print("✅ Connection with SSL requirement successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection with SSL requirement failed: {e}")

# Try 4: Test different sslmode values
print(f"\n4. Testing with different SSL modes:")

ssl_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
for mode in ssl_modes:
    try:
        test_url = PSYCOPG_URL + f"?sslmode={mode}"
        conn = psycopg.connect(test_url)
        print(f"✅ Connection with sslmode={mode} successful!")
        conn.close()
        break
    except Exception as e:
        print(f"❌ Connection with sslmode={mode} failed: {e}")

# Try 5: Use connection dict instead of URL
print(f"\n5. Testing with connection dictionary:")
try:
    conn = psycopg.connect(
        host="sjbwnjqunhonucocaoiu.supabase.co",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="Bravoomega@123"
    )
    print("✅ Connection with dict parameters successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection with dict parameters failed: {e}")
