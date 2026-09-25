# region Import Modules...

import os
from dotenv import load_dotenv
from swiftclient import Connection, exceptions

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

    def __init__(self, auth_url: str, user: str, key: str, auth_version: str) -> None:
        self.auth_url = auth_url
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
            self._conn = Connection(authurl=self.auth_url,
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
