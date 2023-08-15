# wallbox-pwn
Gain root access to Wallbox Pulsar Plus

## Instructions
A computer with both Bluetooth and Wifi is required, only tested on mac.

1. Install bleak (`pip install bleak`)

2. Pwn Wallbox by running the following and following the instructions
```bash
python wallbox-pwn.py
```

3. After reconnecting to your wifi, you can SSH to Wallbox as root using it's IP
```bash
ssh -i id_rsa root@192.168.13.37
```
