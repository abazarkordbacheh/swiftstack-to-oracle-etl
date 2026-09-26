# region Import Modules...

import os
from dotenv import load_dotenv
from utils.utils import max_local_mtime
from swiftclient import Connection, exceptions
from datetime import datetime, timezone

# endregion

# region .env file...

load_dotenv()

auth_url = os.getenv('SWIFT_AUTH_URL')
user = os.getenv('SWIFT_USER')
password = os.getenv('SWIFT_PASSWORD')
container_name = os.getenv('SWIFT_CONTAINER_NAME')
auth_version = os.getenv('SWIFT_AUTH_VERSION')


# endregion


# region Swift Connection...

class SwiftConnection:
    """
    Swift connection class
    """

    def __init__(self, authurl: str, user: str, key: str, auth_version: str) -> None:
        self.authurl = authurl
        self.user = user
        self.key = key
        self.auth_version = auth_version
        self._conn: Connection | None = None

    def connect(self) -> Connection:
        """
        Connect to Swift server
        :return: Connection object
        """
        if self._conn is None:
            self._conn = Connection(authurl=self.authurl,
                                    user=self.user,
                                    key=self.key,
                                    auth_version=self.auth_version)
        return self._conn

    def get_account(self) -> tuple | None:
        """
        Get account information
        :return: Tuple of account information or None
        """
        try:
            headers, containers = self.connect().get_account()
            return headers, containers
        except exceptions.ClientException as exc:
            print(f"Swift connection error: {exc.http_status} — {exc}")
            return None

    def list_objects(self, container: str | None = None) -> list[dict]:
        """
        List all objects in a container.
        Returns a list of dicts with keys like 'name', 'bytes', 'last_modified', etc.
        """
        target = container
        try:
            _, objects = self.connect().get_container(target)
            return objects  # each item is a dict
        except exceptions.ClientException as exc:
            print(f"List error: {exc.http_status} — {exc}")
            return []

    def download_new_objects(
            self,
            container: str,
            prefix: str,
            output_dir: str,
            staging_dir: str | None = None,
            shared_dir: str | None = None,
    ) -> list[str]:
        """
        Download objects from a Swift container that are newer than the most
        recent local file found in output_dir, staging_dir, and shared_dir.

        On the first run (no local files exist), all objects matching the prefix
        are downloaded.

        Object names like 'type_a/table/file.csv' are saved with their basename
        only (file.csv) inside output_dir.

        :param container:   Swift container name.
        :param prefix:      Object name prefix to filter (e.g. 'type_a/' or 'type_b/').
        :param output_dir:  Local directory to save downloaded files.
        :param staging_dir: Optional staging directory to check for already-downloaded files.
        :param shared_dir:  Optional shared directory to check (files moved here are not re-downloaded).
        :return: List of local file paths that were written.
        """

        cutoff: datetime | None = max_local_mtime(output_dir)

        # List remote objects filtered by prefix
        try:
            _, objects = self.connect().get_container(container, prefix=prefix)
        except exceptions.ClientException as exc:
            print(f"List error: {exc.http_status} — {exc}")
            return []

        downloaded: list[str] = []

        for obj in objects:
            name: str = obj['name']
            last_modified_str: str = obj['last_modified']  # ISO 8601, e.g. '2024-01-15T10:30:00.000000'

            # Parse Swift's last_modified (always UTC, no tz info in the string)
            last_modified = datetime.fromisoformat(last_modified_str).replace(tzinfo=timezone.utc)

            # Skip if not newer than local cutoff
            if cutoff is not None and last_modified <= cutoff:
                continue

            # Download the object content
            try:
                _, content = self.connect().get_object(container, name)
            except exceptions.ClientException as exc:
                print(f"Download error for '{name}': {exc.http_status} — {exc}")
                continue

            # Save with basename only (strips prefix/subfolder structure)
            filename = os.path.basename(name)
            local_path = os.path.join(output_dir, filename)

            with open(local_path, 'wb') as f:
                f.write(content)

            print(f"Downloaded: {name} → {local_path}")
            downloaded.append(local_path)

        return downloaded

    def close(self) -> None:
        """
        Close connection
        :return: None
        """
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @classmethod
    def sample(cls) -> 'SwiftConnection':
        """
        Create a SwiftConnection object Sample
        :return: SwiftConnection object
        """
        return SwiftConnection(auth_url, user, password, auth_version)
