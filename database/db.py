import mysql.connector
from mysql.connector import Error
import time
from typing import Optional, Tuple
from contextlib import contextmanager

from ..config import Config
from .models import DatabaseTables

class Database:
    """Database connection and management class"""
    
    def __init__(self):
        self.host = Config.DB_HOST
        self.port = Config.DB_PORT
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self.database = Config.DB_NAME
        self._connection = None
        self._cursor = None

    def connect(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
        """
        Establish connection to MySQL database with retry mechanism
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # First try to connect to MySQL server
                self._connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password
                )
                
                # Create database if it doesn't exist
                self._cursor = self._connection.cursor()
                self._cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                self._cursor.execute(f"USE {self.database}")
                
                # Set connection properties
                self._connection.autocommit = True
                
                print(f"Successfully connected to MySQL database: {self.database}")
                return True
                
            except Error as e:
                print(f"Error connecting to MySQL (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False

    def disconnect(self):
        """Close database connection and cursor"""
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
            print("Database connection closed successfully")
        except Error as e:
            print(f"Error closing database connection: {str(e)}")

    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor
        
        Yields:
            mysql.connector.cursor: Database cursor
        """
        try:
            cursor = self._connection.cursor(dictionary=True)
            yield cursor
            self._connection.commit()
        except Error as e:
            self._connection.rollback()
            print(f"Database error: {str(e)}")
            raise
        finally:
            cursor.close()

    def init_database(self) -> bool:
        """
        Initialize database tables
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                # Create tables
                cursor.execute(DatabaseTables.get_users_table())
                cursor.execute(DatabaseTables.get_playlists_table())
                cursor.execute(DatabaseTables.get_admins_table())
                cursor.execute(DatabaseTables.get_groups_table())
                cursor.execute(DatabaseTables.get_active_streams_table())
                
                print("Database tables initialized successfully")
                return True
                
        except Error as e:
            print(f"Error initializing database: {str(e)}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> Optional[Tuple]:
        """
        Execute a database query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Optional[Tuple]: Query results if any
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                if cursor.with_rows:
                    return cursor.fetchall()
                return None
        except Error as e:
            print(f"Error executing query: {str(e)}")
            return None

    def execute_many(self, query: str, params: list) -> bool:
        """
        Execute multiple database operations
        
        Args:
            query: SQL query string
            params: List of parameter tuples
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, params)
                return True
        except Error as e:
            print(f"Error executing multiple queries: {str(e)}")
            return False

# Create global database instance
db = Database()

def init_db() -> bool:
    """
    Initialize database connection and tables
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    if db.connect():
        return db.init_database()
    return False