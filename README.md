# wallbox-pwn
Gain root access to Wallbox Pulsar Plus

## Instructions
1. Install bleak (`pip install bleak`)

2. Prepare Wallbox for pwnage
```bash
python wb-prepare-update.py
```

3. When given the network name, connect to it, then run upload.sh in another terminal

4. After a seconds, you can SSH to Wallbox as root using
```bash
ssh -i id_rsa root@192.168.13.37
```
