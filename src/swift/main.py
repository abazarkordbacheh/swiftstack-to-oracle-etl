from src.swift.imei import imei
from src.swift.mobile import mobile
from datetime import datetime

print("Starting Programing")
if __name__ == "__main__":
    print("Starting Mobile")
    mobile_start = datetime.now()
    mobile()
    mobile_end = datetime.now()
    print("Ending Mobile")
    print("Mobile took " + str(mobile_end - mobile_start))
    print("-" * 80)

    print("Starting Imei")
    imei_start = datetime.now()
    imei()
    imei_end = datetime.now()
    print("Ending Imei")
    print("Imei took " + str(imei_end - imei_start))
