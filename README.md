# Wallbox pwn

Gain root access to Wallbox Pulsar Plus and Copper SB.
This only works if you are running firmware v5.x.x.
If you are running v6.x.x you can try restoring to original settings to see if your Wallbox came originally with v5.x.x from the factory.
Once rooted, firmware updates shouldn't remove root access.

## Instructions

A computer with both Bluetooth and Wifi is required, tested on OS X and Windows.

1. Install bleak

    ```bash
    pip install bleak
    ```

2. Pwn Wallbox by running the wallbox-pwn script and follow the instructions

    ```bash
    python wallbox-pwn.py
    ```

3. After reconnecting to your wifi, you can SSH to Wallbox as root using its IP and the private key. Example:

    ```bash
    ssh -i id_rsa root@192.168.13.37
    ```

4. Optional, but recommended for security

   1. Create your own private and public key. On your computer run:

        ```bash
        ssh-keygen
        cat ~/.ssh/id_rsa.pub
        ```

   2. On your Wallbox replace the public key with your own (the contents of id_rsa.pub):

        ```bash
        vi ~/.ssh/authorized_keys
        ```
