from paramiko import SSHClient, AutoAddPolicy
from paramiko_expect import SSHClientInteraction
import re


devices = ["192.168.1.3"]


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

            with SSHClientInteraction(client, timeout=1) as ssh:
                for command in kwargs["commands"]:
                    ssh.send(command)
                    ssh.expect()
                    output = ssh.current_output
                    while "more" in ssh.current_output:
                        ssh.send(" ")
                        ssh.expect()
                        output += ssh.current_output
                    
                    output = re.sub("-- more --, next page: Space, continue: g, quit: \^C", "", output)
                    result.append(output)

        return func(result, info)
    return wrapper


@get_prompt
def show_system(result, info):
    lines = [line.strip().split("\n") for line in result]
    for line in lines[0][1:]:
        data = [i.strip(": ") for i in line.split("  ") if i]
        if len(data) > 1:
            info[data[0]] = data[1]
    return info


@get_prompt
def show_interfaces(result, info):
    lines = [line.strip().split("\n") for line in result]
    for line in lines[0][3:]:
        data = [i.strip() for i in line.split(" ") if i]
        if len(data) > 3:
            port = data[1].split("/")[1]
            link = "Up" if data[7] != "Down" else "Down"
            speed = data[7] if data[7] != "Down" else data[3]
            info[port] = {
                "state": data[2]
                "link": link,
                "speed": speed,
                }
    return info


@get_prompt
def show_vlans(result, info):
    port = 1
    lines = [line.strip().split("\n") for line in result]
    for line in lines[0][1:]:
        data = [i.strip() for i in line.split("  ") if i]
        if len(data) > 1 and data[2].isnumeric():
            info[f"{port}"] = {
                "pvid": data[2],
                "frame_type": data[3],
                "ingress_filter": data[4],
                "tx_tag": data[5],
                "uvid": data[6],
                "port_type": data[1],
                "conflict": data[7],
                }
            port += 1
    return info


if __name__ == "__main__":
    show_system(commands = ["show system"])
    show_interfaces(commands = ["show interface * status"])
    show_vlans(commands = ["show vlan status combined interface *"])
