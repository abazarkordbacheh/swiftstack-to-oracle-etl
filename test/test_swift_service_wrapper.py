# ------------------- Import Libraries -------------------
import pytest
from unittest.mock import MagicMock, patch

from src.swift.service import SwiftServiceWrapper


# ------------------- fixtures -------------------
@pytest.fixture
def wrapper():
    """Return a SwiftServiceWrapper configured with dummy credentials."""
    return SwiftServiceWrapper(
        auth_url="http://auth.example.com",
        user="testuser",
        key="testkey",
        auth_version="1",
        container_name="my-container",
    )


# ------------------- __init__ -------------------

class TestInit:
    def test_stores_credentials(self, wrapper):
        """Constructor must persist all supplied credential fields."""
        assert wrapper.auth_url == "http://auth.example.com"
        assert wrapper.user == "testuser"
        assert wrapper.key == "testkey"
        assert wrapper.auth_version == "1"
        assert wrapper.container_name == "my-container"

    def test_service_is_none_initially(self, wrapper):
        """The underlying SwiftService must not be created until first use."""
        assert wrapper._service is None

    def test_options_built_correctly(self, wrapper):
        """_options dict must map credentials to the expected SwiftService keys."""
        assert wrapper._options["os_auth_url"] == "http://auth.example.com"
        assert wrapper._options["os_username"] == "testuser"
        assert wrapper._options["os_password"] == "testkey"


# ------------------- _get_service (lazy) -------------------

class TestGetService:
    @patch("src.swift.service.SwiftService")
    def test_creates_service_on_first_call(self, mock_cls, wrapper):
        """_get_service() must instantiate SwiftService with _options on first call."""
        svc = wrapper._get_service()
        mock_cls.assert_called_once_with(options=wrapper._options)
        assert svc is mock_cls.return_value

    @patch("src.swift.service.SwiftService")
    def test_reuses_existing_service(self, mock_cls, wrapper):
        """Subsequent calls to _get_service() must return the same instance."""
        svc1 = wrapper._get_service()
        svc2 = wrapper._get_service()
        mock_cls.assert_called_once()  # constructed only once
        assert svc1 is svc2


# ------------------- list_objects -------------------

class TestListObjects:
    @patch("src.swift.service.SwiftService")
    def test_returns_list_of_objects(self, mock_cls, wrapper):
        """list_objects() must aggregate listing entries from all successful pages."""
        fake_listing = [{"name": "file1.xlsx"}, {"name": "file2.xlsx"}]
        # Each page yielded by svc.list() must be a dict with 'success' and 'listing'
        fake_page = {"success": True, "listing": fake_listing}
        mock_cls.return_value.list.return_value = iter([fake_page])

        result = wrapper.list_objects()
        assert result == fake_listing

    @patch("src.swift.service.SwiftService")
    def test_returns_empty_list_on_swift_error(self, mock_cls, wrapper):
        """list_objects() must return [] and not propagate a SwiftError."""
        from swiftclient.service import SwiftError
        mock_cls.return_value.list.side_effect = SwiftError("connection failed")

        result = wrapper.list_objects()
        assert result == []

    @patch("src.swift.service.SwiftService")
    def test_returns_empty_list_when_no_objects(self, mock_cls, wrapper):
        """list_objects() must return [] when the container is empty."""
        mock_cls.return_value.list.return_value = iter([])

        result = wrapper.list_objects()
        assert result == []

    @patch("src.swift.service.SwiftService")
    def test_page_failure_returns_empty(self, mock_cls, wrapper):
        """A page with success=False must cause list_objects() to return []."""
        fake_page = {"success": False, "error": "permission denied"}
        mock_cls.return_value.list.return_value = iter([fake_page])

        result = wrapper.list_objects()
        assert result == []


# ------------------- download_object -------------------


class TestDownloadObject:
    @patch("src.swift.service.SwiftService")
    def test_returns_true_on_success(self, mock_cls, wrapper):
        """download_object() must return True when the download result is successful."""
        mock_cls.return_value.download.return_value = iter([{"success": True}])

        result = wrapper.download_object("file1.xlsx", output_dir="/tmp")
        assert result is True

    @patch("src.swift.service.SwiftService")
    def test_returns_false_on_failure(self, mock_cls, wrapper):
        """download_object() must return False when the download result reports failure."""
        mock_cls.return_value.download.return_value = iter([
            {"success": False, "error": "not found"}
        ])

        result = wrapper.download_object("missing.xlsx", output_dir="/tmp")
        assert result is False

    @patch("src.swift.service.SwiftService")
    def test_passes_correct_args_to_download(self, mock_cls, wrapper):
        """download_object() must forward container, object name, and out_directory correctly."""
        mock_cls.return_value.download.return_value = iter([{"success": True}])

        wrapper.download_object("file1.xlsx", output_dir="/data")

        mock_cls.return_value.download.assert_called_once_with(
            container="my-container",
            objects=["file1.xlsx"],
            options={"out_directory": "/data"},
        )


# ------------------- context manager -------------------

class TestContextManager:
    @patch("src.swift.service.SwiftService")
    def test_enter_returns_self(self, mock_cls, wrapper):
        """__enter__ must return the wrapper instance itself."""
        with wrapper as w:
            assert w is wrapper

    @patch("src.swift.service.SwiftService")
    def test_exit_calls_close(self, mock_cls, wrapper):
        """__exit__ must call close() to release the underlying service."""
        wrapper._service = mock_cls.return_value

        with patch.object(wrapper, "close") as mock_close:
            with wrapper:
                pass
            mock_close.assert_called_once()


# ------------------- close -------------------

class TestClose:
    @patch("src.swift.service.SwiftService")
    def test_close_sets_service_to_none(self, mock_cls, wrapper):
        """close() must set _service back to None after releasing the connection."""
        wrapper._service = mock_cls.return_value
        wrapper.close()
        assert wrapper._service is None

    def test_close_without_connection_does_not_raise(self, wrapper):
        """close() must be safe to call when no service has been created yet."""
        assert wrapper._service is None
        wrapper.close()  # must not raise
