from paramiko import SSHClient, AutoAddPolicy
from paramiko_expect import SSHClientInteraction
import re

    
devices = ['192.168.1.3']


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
                username='admin',
                password='admin',
                look_for_keys=False,
                allow_agent=False,
                )

            with SSHClientInteraction(client, timeout=1) as ssh:
                for command in kwargs['commands']:
                    ssh.send(command)
                    ssh.expect()
                    output = ssh.current_output
                    while 'More' in ssh.current_output:
                        ssh.send(' ')
                        ssh.expect()
                        output += ssh.current_output
                    
                    output = re.sub('--More--, q to quit', '', output)
                    result.append(output)

        return func(result, info)
    return wrapper


@get_prompt
def show_system(result, info):
    lines = [line.strip().split('\n') for line in result]
    for line in lines[1][1:]:
        data = [i.strip(': ') for i in line.split('  ') if i]
        if len(data) > 1:
            info[data[0]] = data[1]
    return info


@get_prompt
def show_interfaces(result, info):
    lines = [line.strip().split('\n') for line in result]
    for line in lines[1][3:]:
        data = [i.strip() for i in line.split('  ') if i]
        if len(data) > 3:
            port = data[0].split('/')[0]
            speed = data[4] if data[4] != 'Down' else 'Auto'
            info[port] = {
                'state': data[1],
                'link': data[2],
                'speed': speed,
                }
    return info


@get_prompt
def show_vlans(result, info):
    lines = [line.strip().split('\n') for line in result]
    for line in lines[1][3:]:
        data = [i.strip() for i in line.split('  ') if i]
        if len(data) > 3:
            port = data[0].split('/')[0]
            info[port] = {
                'pvid': data[1],
                'frame_type': data[2],
                'ingress_filter': data[3],
                'tx_tag': data[4],
                'uvid': data[5],
                'port_type': data[6],
                'conflict': data[7],
                }
    return info


if __name__ == '__main__':
    show_system(commands = ['system', 'show'])
    show_interfaces(commands = ['port', 'show status'])
    show_vlans(commands = ['vlan', 'show port-status combined'])
