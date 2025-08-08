"""
Database connection tests.
"""
import pytest
import os
import psycopg
from sqlalchemy import create_engine, text
from urllib.parse import urlparse


class TestDatabaseConnection:
    """Test database connectivity using different methods."""
    
    def test_sqlalchemy_connection(self, database_url, db_engine):
        """Test database connection using SQLAlchemy."""
        with db_engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
            
            # Test PostgreSQL version query
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            assert "PostgreSQL" in version[0]
    
    def test_psycopg_direct_connection(self, database_url):
        """Test direct psycopg connection."""
        # Convert SQLAlchemy URL to psycopg URL
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        
        with psycopg.connect(psycopg_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test")
                result = cur.fetchone()
                assert result[0] == 1
    
    def test_psycopg_connection_with_ssl(self, database_url):
        """Test psycopg connection with SSL requirements."""
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        ssl_url = psycopg_url + "?sslmode=require"
        
        try:
            with psycopg.connect(ssl_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    assert result[0] == 1
        except Exception as e:
            # Some SSL modes might not be available in test environment
            pytest.skip(f"SSL connection test skipped: {e}")
    
    def test_hostname_resolution(self, database_url):
        """Test hostname resolution for the database."""
        import socket
        
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        parsed = urlparse(psycopg_url)
        
        if parsed.hostname:
            try:
                ip = socket.gethostbyname(parsed.hostname)
                assert ip  # Should resolve to some IP
            except socket.gaierror:
                pytest.fail(f"Could not resolve hostname: {parsed.hostname}")
    
    @pytest.mark.parametrize("ssl_mode", ["disable", "allow", "prefer", "require"])
    def test_different_ssl_modes(self, database_url, ssl_mode):
        """Test different SSL modes for database connection."""
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        test_url = psycopg_url + f"?sslmode={ssl_mode}"
        
        try:
            with psycopg.connect(test_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    assert result[0] == 1
        except Exception as e:
            # Some SSL modes might fail in certain environments
            pytest.skip(f"SSL mode {ssl_mode} not supported: {e}")
    
    def test_connection_with_dict_params(self, database_url):
        """Test connection using dictionary parameters."""
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        parsed = urlparse(psycopg_url)
        
        conn_params = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "dbname": parsed.path[1:] if parsed.path else "postgres",
            "user": parsed.username,
            "password": parsed.password
        }
        
        with psycopg.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result[0] == 1
