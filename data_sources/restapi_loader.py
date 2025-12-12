"""
REST API Data Source

Fetches time series data from REST APIs with support for authentication and pagination.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from loguru import logger
import time
from .base import DataSource, DataSourceConfig, DataSourceFactory


class RestAPIDataSource(DataSource):
    """Data source for REST APIs."""

    def __init__(self, config: DataSourceConfig):
        """
        Initialize REST API data source.

        Args:
            config: Data source configuration with parameters:
                - url: API endpoint URL
                - method: HTTP method ("GET" or "POST")
                - auth_type: Authentication type ("none", "basic", "bearer", "api_key")
                - username: Username for basic auth
                - password: Password for basic auth
                - token: Bearer token or API key
                - headers: Additional HTTP headers (dict)
                - params: Query parameters (dict)
                - data: POST request body (dict)
                - json_path: JSONPath to extract data array (e.g., "data.records")
                - time_column: Name of the timestamp column
                - pagination: Enable pagination support
                - pagination_type: "offset", "page", or "cursor"
                - max_pages: Maximum number of pages to fetch
        """
        super().__init__(config)
        self.session = None

    def connect(self) -> bool:
        """Initialize HTTP session."""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from requests.packages.urllib3.util.retry import Retry

            # Create session with retry logic
            self.session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)

            # Setup authentication
            params = self.config.parameters
            auth_type = params.get("auth_type", "none")

            if auth_type == "basic":
                username = params.get("username", "")
                password = params.get("password", "")
                self.session.auth = (username, password)

            elif auth_type == "bearer":
                token = params.get("token", "")
                self.session.headers.update({"Authorization": f"Bearer {token}"})

            elif auth_type == "api_key":
                token = params.get("token", "")
                header_name = params.get("api_key_header", "X-API-Key")
                self.session.headers.update({header_name: token})

            # Add custom headers
            headers = params.get("headers", {})
            if headers:
                self.session.headers.update(headers)

            self.is_connected = True
            logger.info("REST API session initialized")
            return True

        except ImportError as e:
            logger.error(f"Required library not installed: {e}. Install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize API session: {e}")
            return False

    def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            self.session.close()
            self.session = None
            self.is_connected = False
            logger.info("REST API session closed")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        Fetch data from REST API.

        Returns:
            DataFrame with time series data

        Raises:
            Exception if not connected or request fails
        """
        if not self.is_connected:
            raise Exception("Not connected. Call connect() first.")

        params = self.config.parameters
        url = params.get("url")
        if not url:
            raise ValueError("URL parameter is required")

        method = params.get("method", "GET").upper()
        query_params = params.get("params", {})
        post_data = params.get("data", {})
        pagination = params.get("pagination", False)

        all_data = []

        try:
            if pagination:
                all_data = self._fetch_paginated(url, method, query_params, post_data)
            else:
                response_data = self._make_request(url, method, query_params, post_data)
                all_data = self._extract_data(response_data)

            # Convert to DataFrame
            df = pd.DataFrame(all_data)

            # Convert time column to datetime if specified
            time_column = params.get("time_column")
            if time_column and time_column in df.columns:
                df[time_column] = pd.to_datetime(df[time_column])
                df = df.sort_values(time_column).reset_index(drop=True)

            logger.info(f"Fetched {len(df)} rows from REST API")
            self._data = df
            return df

        except Exception as e:
            logger.error(f"Failed to fetch data from API: {e}")
            raise

    def _make_request(self, url: str, method: str, params: Dict, data: Dict) -> Dict:
        """
        Make a single HTTP request.

        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            data: POST data

        Returns:
            Response JSON data
        """
        if method == "GET":
            response = self.session.get(url, params=params, timeout=30)
        elif method == "POST":
            response = self.session.post(url, params=params, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    def _extract_data(self, response_data: Any) -> List[Dict]:
        """
        Extract data array from API response using JSONPath.

        Args:
            response_data: API response (dict or list)

        Returns:
            List of data records
        """
        params = self.config.parameters
        json_path = params.get("json_path", "")

        if not json_path:
            # If no path specified, assume response is the data array
            if isinstance(response_data, list):
                return response_data
            elif isinstance(response_data, dict):
                # Try common keys
                for key in ["data", "results", "records", "items"]:
                    if key in response_data:
                        return response_data[key]
                return [response_data]
            else:
                return []

        # Parse JSONPath
        try:
            import jsonpath_ng
            from jsonpath_ng import parse

            jsonpath_expr = parse(json_path)
            matches = [match.value for match in jsonpath_expr.find(response_data)]

            if matches:
                return matches[0] if isinstance(matches[0], list) else matches
            return []

        except ImportError:
            # Fallback: simple dot notation parsing
            current = response_data
            for key in json_path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return []
            return current if isinstance(current, list) else [current]

    def _fetch_paginated(self, url: str, method: str, params: Dict, data: Dict) -> List[Dict]:
        """
        Fetch data with pagination support.

        Args:
            url: Base URL
            method: HTTP method
            params: Base query parameters
            data: Base POST data

        Returns:
            Combined list of all data records
        """
        config_params = self.config.parameters
        pagination_type = config_params.get("pagination_type", "offset")
        max_pages = config_params.get("max_pages", 10)

        all_data = []
        page = 0
        offset = 0
        cursor = None

        while page < max_pages:
            # Update pagination parameters
            current_params = params.copy()

            if pagination_type == "page":
                current_params["page"] = page
                page_size = config_params.get("page_size", 100)
                current_params["page_size"] = page_size

            elif pagination_type == "offset":
                current_params["offset"] = offset
                limit = config_params.get("limit", 100)
                current_params["limit"] = limit

            elif pagination_type == "cursor" and cursor:
                current_params["cursor"] = cursor

            # Make request
            response_data = self._make_request(url, method, current_params, data)
            page_data = self._extract_data(response_data)

            if not page_data:
                break  # No more data

            all_data.extend(page_data)

            # Update pagination state
            page += 1
            offset += len(page_data)

            # For cursor-based pagination
            if pagination_type == "cursor":
                cursor = response_data.get("next_cursor") or response_data.get("cursor")
                if not cursor:
                    break

            # Check if we've reached the end
            if len(page_data) < config_params.get("page_size", 100):
                break

            # Rate limiting
            time.sleep(0.1)

        return all_data


# Register the data source
DataSourceFactory.register("restapi", RestAPIDataSource)
