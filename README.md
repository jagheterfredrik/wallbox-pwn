# Wallbox pwn

Gain root access to Wallbox Pulsar Plus and Copper SB.
Once rooted, firmware updates shouldn't remove root access.

## Instructions

A computer with both Bluetooth and Wifi is required, tested on OS X and Windows.

1. Install bleak

    ```bash
    pip install bleak
    ```

2. Pwn Wallbox by running the wallbox-pwn script for your version and follow the instructions

    ```bash
    python wallbox-pwn-vX.py
    ```

3. After reconnecting to your wifi, you can SSH to Wallbox as root using its IP and the private key. Example:

    ```bash
    chmod 0600 id_rsa
    ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa -i id_rsa root@192.168.13.37
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
