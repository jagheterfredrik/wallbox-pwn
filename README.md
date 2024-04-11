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
## Error Handling
If you receive the following error when trying to connect to the Wallbox
```bash
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: UNPROTECTED PRIVATE KEY FILE! @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "id_rsa": bad permissions
root@192.168..: Permission denied (publickey).
```
This can be easily fixed by changing the permissions of the certificate.
The following command will do the trick.
```bash
sudo chmod 400 id_rsa
```
