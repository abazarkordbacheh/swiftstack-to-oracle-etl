# region Import Modules...
from swiftclient.service import SwiftService, SwiftError
from typing import Optional, Iterator


# endregion

# region Swift Services...

class SwiftServiceWrapper:
    """
    Wrapper around swiftclient.service.SwiftService.

    SwiftService is designed for bulk/parallel operations and
    returns results as iterators rather than direct values.
    """

    def __init__(
            self,
            auth_url: str,
            user: str,
            key: str,
            auth_version: str = "1",
            container_name: str = "",
    ):
        self.auth_url = auth_url
        self.user = user
        self.key = key
        self.auth_version = auth_version
        self.container_name = container_name

        # SwiftService requires these options.
        self._options = {
            "auth_version": self.auth_version,
            "os_auth_url": self.auth_url,
            "os_username": self.user,
            "os_password": self.key,
        }

        self._service: Optional[SwiftService] = None  # lazy

    def _get_service(self) -> SwiftService:
        """Lazy initialization — only build when needed"""
        if self._service is None:
            self._service = SwiftService(options=self._options)
        return self._service

    def list_objects(self, container: Optional[str] = None) -> list:
        """
        Returns a list of objects in a container.
        Unlike Connection, the result of SwiftService is an iterator.
        """
        container = container or self.container_name
        svc = self._get_service()
        results = []

        try:
            for page in svc.list(container=container):
                if page["success"]:
                    results.extend(page["listing"])
                else:
                    raise SwiftError(page["error"])
        except SwiftError as e:
            print(f"SwiftService list error: {e}")
            return []

        return results

    def download_object(
            self,
            object_name: str,
            output_dir: str,
            container: Optional[str] = None,
    ) -> bool:
        """
        Downloads an object.
        Returns True if successful, False if failed.
        """
        container = container or self.container_name
        svc = self._get_service()

        options = {"out_directory": output_dir}

        try:
            for result in svc.download(
                    container=container,
                    objects=[object_name],
                    options=options,
            ):
                if not result["success"]:
                    print(f"Download failed: {result.get('error')}")
                    return False
        except SwiftError as e:
            print(f"SwiftService download error: {e}")
            return False

        return True

    def close(self) -> None:
        """Closes the connection if it was open"""
        if self._service is not None:
            self._service.__exit__(None, None, None)
            self._service = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
