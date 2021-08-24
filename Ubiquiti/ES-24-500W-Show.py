from paramiko import SSHClient, AutoAddPolicy
from time import sleep
import socket
import re


devices = ["192.168.1.1"]


def get_prompt(func):
    def wrapper(*args, **kwargs):
        info = {}
        result = []
        client = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())

        for device in devices:
            client.connect(
                hostname=device,
                username="admin",
                password="admin",
                look_for_keys=False,
                allow_agent=False,
                )

            with client.invoke_shell() as ssh:
                ssh.send("enable\n")
                ssh.send("admin\n")
                sleep(0.5)
                ssh.recv(60000)

                for command in kwargs["commands"]:
                    ssh.send(f"{command}\n")
                    ssh.settimeout(1)

                    output = ""
                    while True:
                        try:
                            page = ssh.recv(60000).decode("utf-8")
                            output += page
                            sleep(0.5)
                        except socket.timeout:
                            break
                        if "More" in page:
                            ssh.send(" ")

                    output = re.sub("\r", "", output)
                    output = output.replace("--More-- or (q)uit", "")
                    result.append(output)
                    
        return func(result, info)
    return wrapper


@get_prompt
def show_system(result, info):
    lines = [line.split("\n") for line in result]
    for line in lines[0][4:]:
        data = [i.strip() for i in line.split(". ") if i]
        if len(data) > 1:
            data[0] = data[0].replace(".", "")
            info[data[0]] = data[1]
    return info


@get_prompt
def show_interfaces(result, info):
    lines = [line.split("\n") for line in result]
    for line in lines[0][5:]:
        data = [i.strip() for i in line.split("  ") if i]
        if len(data) > 3:
            port = data[0].split("/")[1]
            speed = data[4] if data[2] == "Up" else data[3]
            info[port] = {
                "name": data[1],
                "link": data[2],
                "speed": speed,
                }
    return info


@get_prompt
def show_vlans(result, info):
    lines = [line.split("\n") for line in result]
    for line in lines[0][5:]:
        data = [i.strip() for i in line.split("  ") if i]
        if len(data) > 3:
            port = data[0].split("/")[1]
            info[port] = {
                "pvid": data[1],
                "frame_type": data[3],
                "ingress_filter": data[2],
                "uvid": data[4],
                }
    return info


if __name__ == "__main__":
    show_system(commands = ["show version"])
    show_interfaces(commands = ["show interfaces status all"])
    show_vlans(commands=["show interfaces switchport general"])
