# Wallbox pwn
Gain root access to Wallbox Pulsar Plus

## Instructions
A computer with both Bluetooth and Wifi is required, tested on OS X and Windows.

1. Install bleak (`pip install bleak`)

2. Pwn Wallbox by running the wallbox-pwn script and follow the instructions
```bash
python wallbox-pwn.py
```

3. After reconnecting to your wifi, you can SSH to Wallbox as root using its IP and the private key
```bash
ssh -i id_rsa root@192.168.13.37
```
