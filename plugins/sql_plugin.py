"""
SQL Plugin - Database query plugin for avatar
"""

import logging
from typing import Dict, Optional, List, Any
import re
from datetime import datetime

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class SQLPlugin(BasePlugin):
    """
    SQL plugin for database querying capabilities.
    Supports multiple database backends and safe query execution.
    """
    
    def __init__(self):
        """Initialize SQL plugin"""
        super().__init__()
        self.name = "SQLPlugin"
        self.metadata = {
            'version': '1.0.0',
            'author': 'Avatar Factory',
            'description': 'SQL database query capabilities'
        }
        
        # Database components
        self.connection = None
        self.database_type = None
        self.schemas = []
        self.tables_cache = {}
        
        # Safety settings
        self.read_only = True
        self.max_results = 100
        self.timeout = 30
        
    def initialize(self, config: Dict) -> bool:
        """
        Initialize SQL plugin with configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if initialization successful
        """
        try:
            self.config = config
            
            # Get configuration
            self.database_type = config.get('database', 'sqlite')
            self.schemas = config.get('schemas', [])
            self.read_only = config.get('read_only', True)
            self.max_results = config.get('max_results', 100)
            self.timeout = config.get('timeout', 30)
            
            # Initialize database connection
            self._initialize_database()
            
            # Cache table information
            self._cache_table_info()
            
            logger.info(f"SQL plugin initialized for {self.database_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SQL plugin: {e}")
            return False
    
    def _initialize_database(self):
        """Initialize database connection based on type"""
        if self.database_type == 'postgresql':
            self._setup_postgresql()
        elif self.database_type == 'mysql':
            self._setup_mysql()
        elif self.database_type == 'teradata':
            self._setup_teradata()
        elif self.database_type == 'sqlserver':
            self._setup_sqlserver()
        else:
            self._setup_sqlite()
    
    def _setup_postgresql(self):
        """Setup PostgreSQL connection"""
        try:
            # In production, would use psycopg2 or asyncpg
            connection_params = {
                'host': self.config.get('host', 'localhost'),
                'port': self.config.get('port', 5432),
                'database': self.config.get('database', 'postgres'),
                'user': self.config.get('user'),
                'password': self.config.get('password')
            }
            
            # Mock connection for demo
            self.connection = {'type': 'postgresql', 'params': connection_params}
            logger.info("PostgreSQL connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL: {e}")
            raise
    
    def _setup_mysql(self):
        """Setup MySQL connection"""
        try:
            # In production, would use mysql-connector or aiomysql
            connection_params = {
                'host': self.config.get('host', 'localhost'),
                'port': self.config.get('port', 3306),
                'database': self.config.get('database'),
                'user': self.config.get('user'),
                'password': self.config.get('password')
            }
            
            # Mock connection for demo
            self.connection = {'type': 'mysql', 'params': connection_params}
            logger.info("MySQL connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup MySQL: {e}")
            raise
    
    def _setup_teradata(self):
        """Setup Teradata connection"""
        try:
            # In production, would use teradatasql
            connection_params = {
                'host': self.config.get('host'),
                'user': self.config.get('user'),
                'password': self.config.get('password'),
                'logmech': self.config.get('logmech', 'TD2')
            }
            
            # Mock connection for demo
            self.connection = {'type': 'teradata', 'params': connection_params}
            logger.info("Teradata connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Teradata: {e}")
            raise
    
    def _setup_sqlserver(self):
        """Setup SQL Server connection"""
        try:
            # In production, would use pyodbc or pymssql
            connection_params = {
                'server': self.config.get('server'),
                'database': self.config.get('database'),
                'user': self.config.get('user'),
                'password': self.config.get('password')
            }
            
            # Mock connection for demo
            self.connection = {'type': 'sqlserver', 'params': connection_params}
            logger.info("SQL Server connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup SQL Server: {e}")
            raise
    
    def _setup_sqlite(self):
        """Setup SQLite connection"""
        try:
            import sqlite3
            
            db_path = self.config.get('database_path', ':memory:')
            self.connection = sqlite3.connect(db_path)
            logger.info(f"SQLite connection initialized: {db_path}")
            
        except Exception as e:
            logger.error(f"Failed to setup SQLite: {e}")
            raise
    
    def _cache_table_info(self):
        """Cache table and schema information"""
        try:
            # In production, would query actual database metadata
            # For now, use mock data
            self.tables_cache = {
                'tables': ['users', 'orders', 'products'],
                'schemas': self.schemas,
                'columns': {
                    'users': ['id', 'name', 'email', 'created_at'],
                    'orders': ['id', 'user_id', 'product_id', 'quantity', 'created_at'],
                    'products': ['id', 'name', 'price', 'category']
                }
            }
            
            logger.info(f"Cached info for {len(self.tables_cache['tables'])} tables")
            
        except Exception as e:
            logger.error(f"Failed to cache table info: {e}")
    
    async def process(self, input_data: Dict) -> Optional[Dict]:
        """
        Process SQL-related queries.
        
        Args:
            input_data: Input data with query
            
        Returns:
            Response with SQL results or generated query
        """
        if not self.enabled:
            return None
        
        try:
            content = input_data.get('content', '')
            query_type = self._determine_query_type(content)
            
            if query_type == 'natural_language':
                # Convert natural language to SQL
                sql_query = await self._natural_language_to_sql(content)
                
                # Execute if safe
                if self._is_safe_query(sql_query):
                    results = await self._execute_query(sql_query)
                    return self._format_results(results, sql_query)
                else:
                    return {
                        'content': f"Generated SQL (not executed for safety):\n```sql\n{sql_query}\n```",
                        'metadata': {
                            'plugin': self.name,
                            'query_type': 'generated',
                            'safe': False
                        }
                    }
            
            elif query_type == 'sql':
                # Direct SQL query
                sql_query = self._extract_sql(content)
                
                if self._is_safe_query(sql_query):
                    results = await self._execute_query(sql_query)
                    return self._format_results(results, sql_query)
                else:
                    return {
                        'content': "Query not executed: Only SELECT queries are allowed",
                        'metadata': {
                            'plugin': self.name,
                            'error': 'unsafe_query'
                        }
                    }
            
            return None
            
        except Exception as e:
            return self.handle_error(e, "processing SQL query")
    
    def _determine_query_type(self, content: str) -> str:
        """Determine if input is SQL or natural language"""
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY']
        content_upper = content.upper()
        
        # Check for SQL keywords
        sql_score = sum(1 for keyword in sql_keywords if keyword in content_upper)
        
        if sql_score >= 2 or content_upper.strip().startswith('SELECT'):
            return 'sql'
        
        # Check for database-related natural language
        db_terms = ['database', 'table', 'query', 'show me', 'get', 'find', 'list']
        if any(term in content.lower() for term in db_terms):
            return 'natural_language'
        
        return 'unknown'
    
    async def _natural_language_to_sql(self, query: str) -> str:
        """
        Convert natural language query to SQL.
        
        Args:
            query: Natural language query
            
        Returns:
            SQL query string
        """
        # Simple rule-based conversion (in production, would use LLM)
        query_lower = query.lower()
        
        # Extract table references
        table = None
        for t in self.tables_cache.get('tables', []):
            if t in query_lower:
                table = t
                break
        
        if not table:
            table = 'users'  # Default table
        
        # Build SQL based on patterns
        if 'count' in query_lower:
            return f"SELECT COUNT(*) FROM {table}"
        elif 'all' in query_lower or 'list' in query_lower:
            return f"SELECT * FROM {table} LIMIT {self.max_results}"
        elif 'where' in query_lower:
            # Extract condition (simplified)
            condition = query_lower.split('where')[1].strip()
            return f"SELECT * FROM {table} WHERE {condition} LIMIT {self.max_results}"
        else:
            return f"SELECT * FROM {table} LIMIT 10"
    
    def _extract_sql(self, content: str) -> str:
        """Extract SQL query from content"""
        # Look for SQL in code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        match = re.search(sql_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for SELECT statement
        if 'SELECT' in content.upper():
            lines = content.split('\n')
            sql_lines = []
            in_sql = False
            
            for line in lines:
                if 'SELECT' in line.upper():
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                    if ';' in line:
                        break
            
            return '\n'.join(sql_lines).strip()
        
        return content.strip()
    
    def _is_safe_query(self, query: str) -> bool:
        """
        Check if query is safe to execute.
        
        Args:
            query: SQL query
            
        Returns:
            True if query is safe
        """
        if not self.read_only:
            return True
        
        # Only allow SELECT queries in read-only mode
        query_upper = query.upper().strip()
        
        unsafe_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in unsafe_keywords:
            if keyword in query_upper:
                return False
        
        return query_upper.startswith('SELECT') or query_upper.startswith('WITH')
    
    async def _execute_query(self, query: str) -> List[Dict]:
        """
        Execute SQL query.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results as list of dictionaries
        """
        # Mock execution for demo
        # In production, would execute actual query
        
        logger.info(f"Executing query: {query[:100]}...")
        
        # Return mock results
        return [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
    
    def _format_results(self, results: List[Dict], query: str) -> Dict:
        """
        Format query results for response.
        
        Args:
            results: Query results
            query: Original SQL query
            
        Returns:
            Formatted response
        """
        if not results:
            content = "Query returned no results"
        else:
            # Format as table
            if results:
                headers = list(results[0].keys())
                
                # Create simple text table
                lines = []
                lines.append(' | '.join(headers))
                lines.append('-' * (len(' | '.join(headers))))
                
                for row in results[:10]:  # Limit display
                    values = [str(row.get(h, '')) for h in headers]
                    lines.append(' | '.join(values))
                
                if len(results) > 10:
                    lines.append(f"... and {len(results) - 10} more rows")
                
                content = '\n'.join(lines)
            else:
                content = "No results"
        
        return {
            'content': content,
            'metadata': {
                'plugin': self.name,
                'query': query,
                'row_count': len(results),
                'execution_time': '0.1s'  # Mock
            }
        }
    
    async def cleanup(self):
        """Clean up SQL plugin resources"""
        try:
            # Close database connection
            if self.connection:
                if hasattr(self.connection, 'close'):
                    self.connection.close()
                self.connection = None
            
            # Clear caches
            self.tables_cache.clear()
            
            logger.info("SQL plugin cleaned up")
            
        except Exception as e:
            logger.error(f"Error during SQL plugin cleanup: {e}")
    
    def get_schema_info(self) -> Dict:
        """Get database schema information"""
        return self.tables_cache
    
    def get_statistics(self) -> Dict:
        """Get SQL plugin statistics"""
        return {
            'database_type': self.database_type,
            'schemas': self.schemas,
            'tables': len(self.tables_cache.get('tables', [])),
            'read_only': self.read_only,
            'max_results': self.max_results
        }
