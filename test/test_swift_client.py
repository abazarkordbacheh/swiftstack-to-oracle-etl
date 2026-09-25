# ------------------- Fix Python Path -------------------
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ------------------- Import Libraries -------------------
import pytest
from unittest.mock import MagicMock, patch

# ------------------- Import SwiftConnection -------------------
from src.swift.client import SwiftConnection


class TestSwiftConnection:
    """Unit test for SwiftConnection"""

    # Test Values
    AUTH_URL = "http://swift.example.com/auth/v1.0"
    USER = "testuser"
    KEY = "testpassword"
    AUTH_VERSION = "1"

    def test_init_stores_credentials(self):
        """Check that __init_ is saved correctly"""
        conn = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )

        assert conn.auth_url == self.AUTH_URL
        assert conn.user == self.USER
        assert conn.key == self.KEY
        assert conn._conn is None  # lazy

    @patch("src.swift.client.Connection")
    def test_connect_creates_connection(self, mock_connection_class):
        """Check if connect() creates a Connection"""
        mock_conn_instance = MagicMock()
        mock_connection_class.return_value = mock_conn_instance

        swift = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        swift.connect()

        # Connection must be called with the correct parameters
        mock_connection_class.assert_called_once_with(
            authurl=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        assert swift._conn is mock_conn_instance

    @patch("src.swift.client.Connection")
    def test_connect_is_lazy(self, mock_connection_class):
        """Check that connect is not called twice"""
        mock_connection_class.return_value = MagicMock()

        swift = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        swift.connect()
        swift.connect()  # Second time

        # Must only be created once
        mock_connection_class.assert_called_once()

    @patch("src.swift.client.Connection")
    def test_get_account_returns_data(self, mock_connection_class):
        """Check if get_account returns data"""
        fake_account_data = ({"content-type": "text/plain"}, [{"name": "container1"}])
        mock_conn = MagicMock()
        mock_conn.get_account.return_value = fake_account_data
        mock_connection_class.return_value = mock_conn

        swift = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        result = swift.get_account()

        assert result == fake_account_data

    @patch("src.swift.client.Connection")
    def test_get_account_handles_exception(self, mock_connection_class):
        """Check that SwiftStack catches the error and returns None"""
        from swiftclient.exceptions import ClientException

        mock_conn = MagicMock()
        mock_conn.get_account.side_effect = ClientException("auth failed")
        mock_connection_class.return_value = mock_conn

        swift = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        result = swift.get_account()

        assert result is None

    @patch("src.swift.client.Connection")
    def test_context_manager(self, mock_connection_class):
        """Context manager check — with SwiftConnection(...) as s"""
        mock_connection_class.return_value = MagicMock()

        with SwiftConnection(
                auth_url=self.AUTH_URL,
                user=self.USER,
                key=self.KEY,
                auth_version=self.AUTH_VERSION,
        ) as swift:
            assert swift is not None

    def test_close_without_connect(self):
        """Check that close() does not throw an error without connect()"""
        swift = SwiftConnection(
            auth_url=self.AUTH_URL,
            user=self.USER,
            key=self.KEY,
            auth_version=self.AUTH_VERSION,
        )
        swift.close()  # You should not throw an exception
