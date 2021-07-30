from paramiko import SSHClient, AutoAddPolicy
from datetime import datetime
import re


start_time = datetime.now()

def send_show_command(
    devices,
    username,
    password,
    command,
    max_bytes=60000,
    delay=1,
    ):

    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())

    info = {}
    for device in devices:
        print(f'\n---------- Connecting device {device} ----------\n')
        client.connect(
            hostname=device,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False,
            )

        stdin, stdout, sterr = client.exec_command(command)
        output = stdout.readlines()
        for line in output[3:]:
            data = [i.strip() for i in line.split('  ') if i]
            if re.search('[a-zA-Z]', data[0]):
                interface = data[0]
                info[interface] = {
                    'ip': [data[1]],
                    'state': data[2].split('/')[0],
                    'link': data[2].split('/')[1],
                    'description': data[3],
                    }
            else:
                info[interface]['ip'].append(data[0])
        print(info)


if __name__ == '__main__':
    devices = ['192.168.1.1', '192.168.1.2']
    command = '/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces'
    send_show_command(devices, 'ubnt', 'ubnt', command)
    run_time = datetime.now() - start_time
    print(f'\n---------- Elapsed time: {run_time} ----------\n')
