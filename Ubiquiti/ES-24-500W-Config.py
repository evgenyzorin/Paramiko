from paramiko import SSHClient, AutoAddPolicy
from time import sleep
import socket
import re


DEVICES = 'Devices.txt'
COMMANDS = 'Commands.txt'


def get_devices(devices):
    with open(devices) as f:
        lines = [line for line in f.read().splitlines()]
    return lines


def get_commands(commands):
    with open(commands) as f:
        lines = [line for line in f.read().splitlines()]
    return lines


def update_system(devices, username, password, enable, commands):

    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())

    for device in devices:
        print(f"\n----- Connecting to device {device} -----\n")
        client.connect(
            hostname=device,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False,
            )

        with client.invoke_shell() as ssh:
            ssh.send("enable\n")
            ssh.send(f"{enable}\n")
            sleep(0.5)
            ssh.recv(60000)

            for command in commands:
                ssh.send(f"{command}\n")
                ssh.settimeout(1)

                output = ""
                while True:
                    try:
                        page = ssh.recv(60000).decode("utf-8")
                        output += page.strip()
                        sleep(1)
                    except socket.timeout:
                        break
                    if "More" in page:
                        ssh.send(" ")

                output = re.sub("\r", "", output)
                output = output.replace("--More-- or (q)uit", "")
                print(f"{output}\n")
            print("\n-------------------- Done! --------------------\n")


if __name__ == "__main__":
    devices = get_devices(DEVICES)
    commands = get_commands(COMMANDS)
    update_system(devices, "username", "password", "enable", commands)
