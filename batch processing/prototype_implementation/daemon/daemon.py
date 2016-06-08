# This script run on each ec2 instance, receive command from controller

import sh
import os
import re
import json
import socket
import subprocess

from sh import ErrorReturnCode
from subprocess import PIPE

# mount a filesystem
def mount_fs(dev_name, dst):
    if not os.path.exists(dst):
        os.mkdir(dst)

    try:
        res = sh.sudo.mount(dev_name, dst)
    except ErrorReturnCode:
        print('Error when mounting filesystem.' )


# Run a job on Docker container
def run_job(image_name, cmd, cpu_set, cpu_shares = 1024):
    print 'Creating container: %s...',

    command = ['sudo docker run -itd --cpuset-cpus={cpuset} --cpu-shares {cpuShares} {image} {running_cmd}'.format(
        cpuset = cpu_set, cpuShares = cpu_shares, image = image_name, running_cmd = cmd)]

    proc = subprocess.Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
    container_id, err = proc.communicate()


    return container_id


# Import an image to Docker
def import_image(filename):
    print 'Importing image %s to Docker...' % filename,

    command = ['sudo docker load --input=' + filename]

    proc = subprocess.Popen(command, shell = True)
    res,err = proc.communicate()

    print 'Done'

    return res


# Export filesystem of a finished container
def export_fs(container_id, dst_filename):
    command = ['sudo docker export --output=%s container_id' % dst_filename]

    proc = subprocess.Popen(command, shell = True)
    res,err = proc.communicate()

    return res


# Remove a container
def remove_containers(container_ids):
    command = ['sudo docker rm ' + container_ids]
    command += ['docker']
    command += ['rm']
    command += container_ids

    proc = subprocess.Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
    res,err = proc.communicate()

    return res

# Stop a container
def stop_container(container_ids):
    command = ['sudo docker stop ' + container_ids]

    proc = subprocess.Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
    # res,err = proc.communicate()
    res = 'succeed!'

    return res


# Check status of containers
def check_status(ids = None):
    get_id_cmd = ['sudo docker ps -q']

    if not ids:
        get_id_proc = subprocess.Popen(get_id_cmd, shell = True, stdout = PIPE, stderr = PIPE)
        ids, err = get_id_proc.communicate()

        if err:
            print err

    container_list = []
    if ids:
        ids = ids.strip().split('\n')
    else:
        ids = []

    for cid in ids:
        inspect_container_cmd = ['sudo docker inspect %s' % cid]
        inspect_container_proc = subprocess.Popen(inspect_container_cmd, shell = True, stdout = PIPE, stderr = PIPE)
        data,err = inspect_container_proc.communicate()

        if err:
            print err

        data = json.loads(data)

        # get cpu shares info
        get_cpu_shares_cmd = ['cat /sys/fs/cgroup/cpu/docker/%s/cpu.shares' % data[0]['Id']]
        get_cpu_shares_proc = subprocess.Popen(get_cpu_shares_cmd, shell = True, stdout = PIPE, stderr = PIPE)
        cpu_shares,err = get_cpu_shares_proc.communicate()

        if not cpu_shares:
            cpu_shares = '0'

        if err:
            print err

        # get cpuset info
        get_cpuset_cpus_cmd = ['cat /sys/fs/cgroup/cpuset/docker/%s/cpuset.cpus' % data[0]['Id']]
        get_cpuset_cpus_proc = subprocess.Popen(get_cpuset_cpus_cmd, shell = True, stdout = PIPE, stderr = PIPE)
        cpuset_cpus,err = get_cpuset_cpus_proc.communicate()

        if err:
            print err

        container_list.append({'id' : cid,
                               'full_id': data[0]['Id'],
                               'cpu_shares' : int(cpu_shares.strip()),
                               'cpuset_cpus': cpuset_cpus,
                               'state': data[0]['State']})

    return container_list

# Check spot fail
def check_termination():
    res = sh.curl('-s', 'http://169.254.169.254/latest/meta-data/spot/termination-time')
    mat = re.match('.*T.*Z', str(res))

    # return True if the instance is marked as termination
    return not mat == None

# set cpu-shares of a container
def set_cpu_shares(container_id, weight):
    command = ['sudo cgset -r cpu.shares=%s docker/%s' % (weight, container_id)]

    proc = subprocess.Popen(command, shell = True)
    proc.communicate()


def set_cpuset_cpus(container_id, core):
    command = ['sudo cgset -r cpuset.cpus=%s docker/%s' % (core, container_id)]

    proc = subprocess.Popen(command, shell = True)
    proc.communicate()


# parse input string
def parse_input(input_str):
    # inputs should be in the format cmd:args
    terms = input_str.split('$')
    cmd = terms[0]
    args = terms[1].strip().split('|')

    return (cmd, args)





if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (socket.gethostname(), 10086)
    print ('Daemon starts on %s port %d' % server_address )
    sock.bind(server_address)

    sock.listen(5)

    while True:
        conn, client_address = sock.accept()

        try:
            print ('get connection from ', client_address)

            # 1024 bytes should be enough
            data = conn.recv(1024)
            cmd, args = parse_input(data)

            if cmd == 'run':
                if (len(args) == 3):
                    res = run_job(args[0], args[1], args[2])
                elif (len(args) > 3):
                    res = run_job(args[0], args[1], args[2], cpu_shares = int(args[3]))
                else:
                    print ('Error, 3 or more arguments required.')
                    res = ''

                conn.sendall(res)

            elif cmd == 'load':
                if args:
                    res = import_image(args[0])
                else:
                    res = ''

                conn.sendall(res)
            elif cmd == 'export':
                if len(args) >= 2:
                    res = export_fs(args[0], args[1])
                else:
                    print ('Error, 2 arguments required')
                    res = ''

                conn.sendall(res)
            elif cmd == 'rm':
                if args:
                    res = remove_containers(args[0])
                else:
                    res = ''

                conn.sendall(res)
            elif cmd == 'stop':
                if args:
                    res = stop_container(args[0])
                else:
                    res = ''

                conn.sendall(res)
            elif cmd == 'stat':
                status = check_status()

                conn.sendall(json.dumps(status))
            elif cmd == 'isTerminate':
                if check_termination:
                    res = '1'
                else:
                    res = ''

                conn.sendall(res)
            elif cmd == 'setcpu':
                assert(len(args) >= 2)
                set_cpu_shares(args[0], args[1])

                conn.sendall('Done')
            elif cmd == 'set_cpuset_cpus':
                assert(len(args) >= 2)
                set_cpuset_cpus(args[0], args[1])

            elif cmd == 'inspect':
                assert(len(args) > 0)
                res = check_status(args[0])

                data = json.dumps(res)

                conn.sendall(data)
            else:
                conn.sendall('Error, unexpected command...')

        finally:
            conn.close()



