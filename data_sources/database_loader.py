"""
Database Data Source

Loads time series data from SQL databases (PostgreSQL, MySQL, SQLite, SQL Server).
"""

from typing import Optional, Dict, Any
import pandas as pd
from loguru import logger
from .base import DataSource, DataSourceConfig, DataSourceFactory


class DatabaseDataSource(DataSource):
    """Data source for SQL databases."""

    def __init__(self, config: DataSourceConfig):
        """
        Initialize database data source.

        Args:
            config: Data source configuration with parameters:
                - db_type: Database type ("postgresql", "mysql", "sqlite", "mssql")
                - host: Database host (not needed for SQLite)
                - port: Database port (not needed for SQLite)
                - database: Database name or file path (for SQLite)
                - username: Database username (not needed for SQLite)
                - password: Database password (not needed for SQLite)
                - table: Table name to query
                - query: Custom SQL query (optional, overrides table)
                - time_column: Name of the timestamp column
        """
        super().__init__(config)
        self.connection = None
        self.db_type = config.parameters.get("db_type", "sqlite")

    def connect(self) -> bool:
        """Connect to the database."""
        try:
            import sqlalchemy
            from sqlalchemy import create_engine

            params = self.config.parameters
            db_type = params.get("db_type", "sqlite")

            # Build connection string based on database type
            if db_type == "sqlite":
                database = params.get("database", ":memory:")
                conn_str = f"sqlite:///{database}"

            elif db_type == "postgresql":
                host = params.get("host", "localhost")
                port = params.get("port", 5432)
                database = params.get("database", "")
                username = params.get("username", "")
                password = params.get("password", "")
                conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"

            elif db_type == "mysql":
                host = params.get("host", "localhost")
                port = params.get("port", 3306)
                database = params.get("database", "")
                username = params.get("username", "")
                password = params.get("password", "")
                conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

            elif db_type == "mssql":
                host = params.get("host", "localhost")
                port = params.get("port", 1433)
                database = params.get("database", "")
                username = params.get("username", "")
                password = params.get("password", "")
                conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

            else:
                logger.error(f"Unsupported database type: {db_type}")
                return False

            # Create engine and test connection
            self.connection = create_engine(conn_str)
            with self.connection.connect() as conn:
                logger.info(f"Successfully connected to {db_type} database")

            self.is_connected = True
            return True

        except ImportError as e:
            logger.error(f"Required library not installed: {e}. Install with: pip install sqlalchemy pymysql pyodbc")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.connection:
            self.connection.dispose()
            self.connection = None
            self.is_connected = False
            logger.info("Disconnected from database")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        Load data from database.

        Returns:
            DataFrame with time series data

        Raises:
            Exception if not connected or query fails
        """
        if not self.is_connected:
            raise Exception("Not connected to database. Call connect() first.")

        params = self.config.parameters

        # Use custom query if provided, otherwise query the table
        if "query" in params and params["query"]:
            query = params["query"]
        else:
            table = params.get("table")
            if not table:
                raise ValueError("Either 'table' or 'query' parameter must be provided")
            query = f"SELECT * FROM {table}"

        try:
            # Load data using pandas
            df = pd.read_sql(query, self.connection)

            # Convert time column to datetime if specified
            time_column = params.get("time_column")
            if time_column and time_column in df.columns:
                df[time_column] = pd.to_datetime(df[time_column])
                df = df.sort_values(time_column).reset_index(drop=True)

            logger.info(f"Loaded {len(df)} rows from database")
            self._data = df
            return df

        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            raise

    def get_tables(self) -> list:
        """
        Get list of available tables in the database.

        Returns:
            List of table names
        """
        if not self.is_connected:
            logger.warning("Not connected to database")
            return []

        try:
            from sqlalchemy import inspect
            inspector = inspect(self.connection)
            tables = inspector.get_table_names()
            return tables
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []

    def get_columns(self, table: str) -> list:
        """
        Get column names for a specific table.

        Args:
            table: Table name

        Returns:
            List of column names
        """
        if not self.is_connected:
            logger.warning("Not connected to database")
            return []

        try:
            from sqlalchemy import inspect
            inspector = inspect(self.connection)
            columns = [col['name'] for col in inspector.get_columns(table)]
            return columns
        except Exception as e:
            logger.error(f"Failed to get columns for table {table}: {e}")
            return []


# Register the data source
DataSourceFactory.register("database", DatabaseDataSource)
