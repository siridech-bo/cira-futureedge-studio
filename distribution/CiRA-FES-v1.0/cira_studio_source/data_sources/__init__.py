"""Data source connectors and loaders."""

# Import all data sources to trigger their registration
from .csv_loader import CSVDataSource
from .edgeimpulse_loader import EdgeImpulseDataSource
from .database_loader import DatabaseDataSource
from .restapi_loader import RestAPIDataSource
from .streaming_loader import StreamingDataSource

__all__ = [
    "CSVDataSource",
    "EdgeImpulseDataSource",
    "DatabaseDataSource",
    "RestAPIDataSource",
    "StreamingDataSource",
]
