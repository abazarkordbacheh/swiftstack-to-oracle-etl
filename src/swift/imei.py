# region Import Modules...

import os
from dotenv import load_dotenv
from src.swift.client import SwiftConnection


# endregion


# region mobile function...

def imei():
    load_dotenv()
    AUTHURL = os.getenv('SWIFT_AUTH_URL')
    USER = os.getenv('SWIFT_USER')
    PASSWORD = os.getenv('SWIFT_PASSWORD')
    CONTAINER_NAME = os.getenv('CONTAINER_NAME')
    AUTH_VERSION = os.getenv('SWIFT_AUTH_VERSION')
    OUT_PUT_DIR = os.getenv('IMEI_OUT_PUT_DIR')
    PREFIX = os.getenv('IMEI_PERFIX')

    conn = SwiftConnection(AUTHURL, USER, PASSWORD, AUTH_VERSION)

    count_file = conn.download_new_objects(CONTAINER_NAME, PREFIX, OUT_PUT_DIR)
    print(f"Count of files : {len(count_file)}")
    print("Mobile Download Completed")

# endregion
