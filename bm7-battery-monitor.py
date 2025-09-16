# bm7-battery-monitor - Read data from Ancel BM300 Pro BLE battery monitors
# https://github.com/slydiman/bm7-battery-monitor
# Based on the following code:
# https://github.com/JeffWDH/bm6-battery-monitor

# pip uninstall crypto
# pip uninstall pycrypto
# pip install pycryptodome

# pip install bleak

import argparse
import json
import asyncio

from Crypto.Cipher import AES
from bleak import BleakClient
from bleak import BleakScanner

# Function to scan for BM7 devices
async def scan_bm7(format):
  device_list = []
  scan = await BleakScanner.discover(return_adv=True, timeout=7)

  # Filter only Ancel BM300 Pro devices
  for device in scan.values():
    if device[0].name == "BM300 Pro":
      device_list.append([device[0].address, device[1].rssi])

  # Output data
  if format == "ascii":
    if device_list:
      print("Address           RSSI")
      for item in device_list:
        print(item[0] + " " + str(item[1]))
    else:
      print("No Ancel BM300 Pro devices found.")
  if format == "json":
    print(json.dumps(device_list))

# Function to connect to a Ancel BM300 Pro and pull voltage and temperature readings
# Note: Temperature readings are in Celsius and do not go below 0C
async def get_bm7_data(address, format):
  # The Ancel BM300 Pro encryption key is only /slightly/ different than the BM2
  key=bytearray([108, 101, 97, 103, 101, 110, 100, 255, 254, 48, 49, 48, 48, 48, 48, 64])

  bm7_data = {
    "voltage": "",
    "temperature": "",
    "soc": ""
  }

  def decrypt(crypted):
    cipher = AES.new(key, AES.MODE_CBC, 16 * b'\0')
    decrypted = cipher.decrypt(crypted).hex()
    return decrypted

  def encrypt(plaintext):
    cipher = AES.new(key, AES.MODE_CBC, 16 * b'\0')
    encrypted = cipher.encrypt(plaintext)
    return encrypted

  async def notification_handler(sender, data):
    message = decrypt(data)
    if message[0:8] == "d1550700": # Ignore d15507ff000000000000000000000000
      bm7_data["voltage"] = int(message[15:18],16) / 100
      bm7_data["soc"] = int(message[12:14],16)
      if message[6:8] == "01":
        bm7_data["temperature"] = -int(message[8:10],16)
      else:
        bm7_data["temperature"] = int(message[8:10],16)

  async with BleakClient(address, timeout=30) as client:
    # The d15507 command tells the Ancel BM300 Pro to start sending volt/temp notifications
    await client.write_gatt_char("FFF3", encrypt(bytearray.fromhex("d1550700000000000000000000000000")), response=True)

    # Subscribe to notifications
    await client.start_notify("FFF4", notification_handler)

    # Wait for readings
    while not bm7_data["voltage"] and not bm7_data["temperature"]:
      await asyncio.sleep(0.1)

    # Clean up
    await client.stop_notify("FFF4")

    # Output data
    if format == "ascii":
      print("Voltage: " + str(bm7_data["voltage"]) + "V")
      print("Temperature: " + str(bm7_data["temperature"]) + "C")
      print("SoC: " + str(bm7_data["soc"]) + "%")
    if format == "json":
      print(json.dumps(bm7_data))

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--format", choices=["ascii", "json"], default="ascii", help="Output format")
  req = parser.add_mutually_exclusive_group(required=True)
  req.add_argument("--address", metavar="<address>", help="Address of Ancel BM300 Pro to poll data from")
  req.add_argument("--scan", action="store_true", help="Scan for available Ancel BM300 Pro devices")
  args = parser.parse_args()
  if args.address:
    try:
      asyncio.run(get_bm7_data(args.address, args.format))
    except Exception as e:
      print(e)
  if args.scan:
    try:
      asyncio.run(scan_bm7(args.format))
    # Don't hide errors like "The Bluetooth device is not ready for use."
    except Exception as e:
      print(e)
