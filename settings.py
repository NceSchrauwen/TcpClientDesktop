import json
import os

SETTINGS_FILE = "settings.json"

if not os.path.exists(SETTINGS_FILE):
    raise FileNotFoundError("Missing settings.json file!")

with open(SETTINGS_FILE, "r") as f:
    settings = json.load(f)

PI_IP = settings.get("pi_ip", "192.168.2.30")
PORT = settings.get("port", 12345)
