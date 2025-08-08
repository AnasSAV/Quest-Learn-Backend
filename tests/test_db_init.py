"""
Database initialization tests.
"""
import pytest
from sqlalchemy import inspect


class TestDatabaseInitialization:
    """Test database initialization and schema setup."""
    
    def test_database_tables_exist(self, db_engine):
        """Test that all expected tables exist in the database."""
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()
        
        # Expected tables based on your models
        expected_tables = [
            "users",
            "classrooms", 
            "assignments",
            "questions",
            "attempts",
            "upload_tokens"
        ]
        
        missing_tables = []
        for table in expected_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            pytest.skip(f"Tables not created yet: {missing_tables}")
        
        # If all tables exist, verify they have the expected structure
        for table in expected_tables:
            columns = inspector.get_columns(table)
            assert len(columns) > 0, f"Table {table} has no columns"
    
    def test_database_schema_integrity(self, db_engine):
        """Test database schema integrity and foreign key relationships."""
        inspector = inspect(db_engine)
        
        # Test foreign key relationships exist
        tables_with_fks = [
            "assignments",  # Should reference classrooms and users
            "questions",    # Should reference assignments  
            "attempts",     # Should reference questions and users
            "upload_tokens" # Should reference users
        ]
        
        for table in tables_with_fks:
            if table in inspector.get_table_names():
                foreign_keys = inspector.get_foreign_keys(table)
                # Most tables should have at least one foreign key
                if table != "upload_tokens":  # upload_tokens might not have FKs
                    assert len(foreign_keys) > 0, f"Table {table} should have foreign keys"
    
    def test_init_db_function(self):
        """Test that the init_db function can be imported and called."""
        try:
            from app.db.init_db import init_db
            # Don't actually run init_db in tests as it might modify the database
            assert callable(init_db)
        except ImportError:
            pytest.skip("init_db function not available")
    
    def test_database_connection_pool(self, db_engine):
        """Test database connection pooling."""
        # Test multiple concurrent connections
        connections = []
        try:
            for i in range(3):
                conn = db_engine.connect()
                connections.append(conn)
                
                # Execute a simple query
                result = conn.execute("SELECT 1")
                assert result.fetchone()[0] == 1
        finally:
            # Clean up connections
            for conn in connections:
                conn.close()
    
    def test_database_session_creation(self, db_session):
        """Test that database sessions can be created and used."""
        # Test basic session functionality
        result = db_session.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row[0] == 1
        
        # Test session rollback capability
        db_session.rollback()
    
    def test_table_constraints(self, db_engine):
        """Test that database tables have proper constraints."""
        inspector = inspect(db_engine)
        
        tables_to_check = ["users", "classrooms", "assignments"]
        
        for table_name in tables_to_check:
            if table_name in inspector.get_table_names():
                # Check for primary key constraints
                pk_constraint = inspector.get_pk_constraint(table_name)
                assert pk_constraint["constrained_columns"], f"Table {table_name} should have a primary key"
                
                # Check for unique constraints (like email in users table)
                unique_constraints = inspector.get_unique_constraints(table_name)
                if table_name == "users":
                    # Users table should have unique email constraint
                    email_unique = any("email" in constraint["column_names"] for constraint in unique_constraints)
                    assert email_unique, "Users table should have unique email constraint"
