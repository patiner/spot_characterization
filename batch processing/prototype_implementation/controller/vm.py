from __future__ import print_function

import time
import sys
import os
import subprocess
import pipes
import boto
import boto.ec2
import boto.manage.cmdshell

from sys import stderr
from threading import Lock

# input your EC2 access ID and access key here
EC2_ACCESS_ID  = 'A***Q'
EC2_ACCESS_KEY = 'R***I'

class VM:
    """
    This class store information about a VM
    """

    # variables use to launch an instance
    ec2_id = EC2_ACCESS_ID
    ec2_key = EC2_ACCESS_KEY

    def __init__(self,
                 image_id,
                 key_name,
                 key_file,
                 user_name,
                 zone = None,
                 bidding = None,
                 region = 'us-east-1',
                 security_groups = ['default'],
                 user_data = None,
                 instance_type = 'm1.small'):
        self.inst_id = image_id
        self.inst_key_name = key_name
        self.inst_key_file = key_file
        self.inst_user_name = user_name
        self.spot_bidding = bidding
        self.ec2_region = region
        self.inst_security_groups = security_groups
        self.inst_user_data = user_data
        self.inst_type = instance_type
        self.zone = zone

        self.state = 'unlaunched'
        self.conn = None
        self.instance = None
        self.spot_reqs = None
        self.reservation = None
        self.sshclient = None
        self.processes = {}
        self.lock = Lock()

    def launch_instance(self):
        with self.lock:
            try:
                self.conn = boto.ec2.connect_to_region(self.ec2_region,
                                                  aws_access_key_id = self.ec2_id,
                                                  aws_secret_access_key = self.ec2_key)
            except Exception as e:
                print((e), file=stderr)
                sys.exit(1)

            print("Launching VM...")
            if self.spot_bidding:
                # launch spot instance
                print("Requesting spot instance with price $%.3f" % self.spot_bidding)
                self.spot_reqs = self.conn.request_spot_instances(
                        price = self.spot_bidding,
                        image_id = self.inst_id,
                        key_name = self.inst_key_name,
                        instance_type = self.inst_type,
                        placement = self.zone,
                        user_data = self.inst_user_data)
                req_ids = [req.id for req in self.spot_reqs]
                req_count = len(req_ids)

                print("Waiting for spot instances to be granted. This could take a few minutes...")

                try:
                    while True:
                        time.sleep(30)
                        reqs = self.conn.get_all_spot_instance_requests()
                        id_to_reqs = {}
                        for r in reqs:
                            id_to_reqs[r.id] = r
                        active_instance_ids = []
                        for id in req_ids:
                            if id in id_to_reqs and id_to_reqs[id].state == "active":
                                active_instance_ids.append(id_to_reqs[id].instance_id)
                            elif id in id_to_reqs and id_to_reqs[id].state == "cancelled":
                                req_count -= 1
                            elif id in id_to_reqs and id_to_reqs[id].status.code == "price-too-low":
                                print("Canceling spot request {req}, price too low.".
                                        format(req = id))
                                self.conn.cancel_spot_instance_requests([id])
                                return False
                        if len(active_instance_ids) == req_count:
                            if req_count:
                                print("Spot instance granted!")
                                resv = self.conn.get_all_reservations(active_instance_ids)
                                self.reservation = resv[0]
                                self.instance = self.reservation.instances[0]
                                self.state = self.instance.state
                                break
                            else:
                                print("No open spot requests.")
                                self.spot_reqs = None
                                return False
                except:
                    print("Canceling spot instance requests...")
                    self.conn.cancel_spot_instance_requests(req_ids)
                    sys.exit(0)
            # launch on-demand instance
            else:
                resv = self.conn.run_instances(image_id = self.inst_id,
                                         key_name = self.inst_key_name,
                                         security_groups = self.inst_security_groups,
                                         instance_type = self.inst_type,
                                         user_data = self.inst_user_data,
                                         placement = self.zone)
                self.reservation = resv
                self.instance = resv.instances[0]
                self.state = self.instance.state
                print('VM %s has been launched successfully!' % self.instance.id)

            print("Instance initializing...")
            while self.instance.update() != 'running':
                time.sleep(5)
            print("Done. Instance is running.")

    def terminate_instance(self, status = ''):
        with self.lock:
            if self.instance:
                if status:
                    print('%s terminating instance %s...' % (TERMINATE_STATUS[status], self.instance.id))
                self.instance.terminate()
                self.state = 'unlaunched'
                print('%s terminated successfully!' % self.instance.id)
                self.instance = None
            elif self.spot_reqs:
                print("Caceling spot request...")
                self.conn.cancel_spot_instance_requests([req.id for req in self.spot_reqs])
                self.spot_reqs = None
            else:
                print("No running instances or spot requests.")

    def ssh_instance(self):
        while self.instance.update() != 'running':
            if self.instance.update() == 'terminated':
                print ('The instance %s has terminated.' % self.instance.id)
                sys.exit(0)
            print('The instance is %s, sleep 45s...' % self.instance.state)
            time.sleep(45)

        try:
            self.sshclient = boto.manage.cmdshell.sshclient_from_instance(self.instance,
                                                                          self.inst_key_file,
                                                                          user_name = self.inst_user_name)
        except:
            print('SSH fail, try to reconnect after 30s...')
            time.sleep(30)
            self.sshclient = boto.manage.cmdshell.sshclient_from_instance(self.instance,
                                                                          self.inst_key_file,
                                                                          user_name = self.inst_user_name)
        try:
            self.sshclient.exists('/')
        except UnboundLocalError, AttributeError:
            print('SSH fail, try to reconnect after 30s...')
            time.sleep(30)
            self.sshclient = boto.manage.cmdshell.sshclient_from_instance(self.instance,
                                                                          self.inst_key_file,
                                                                          user_name = self.inst_user_name)


    def put_file_from_local(self, src, dst):
        attempt = 0
        while True:
            if self.instance and self.instance.public_dns_name:
                args = ['scp']
                args += ['-i', self.inst_key_file]
                args += ['-o', 'StrictHostKeyChecking=no']
                args += ['-o', 'UserKnownHostsFile=/dev/null']
                args += [src]
                args += ['%s@%s:' % (self.inst_user_name, self.instance.public_dns_name) +
                        dst]

                print("putting file {filename} to {user}@{host}...".
                        format(filename = src,
                               user = self.inst_user_name,
                               host = self.instance.public_dns_name))

                with open(os.devnull, 'w') as FNULL:
                    proc = subprocess.Popen(args, stdout = FNULL, stderr = subprocess.STDOUT)
                    status = proc.wait()

                if status == 0:
                    break
                elif attempt >= 5:
                    raise RuntimeError("put file from local fails with error %s" %
                            proc.returncode)
                else:
                    print("Error {0} while putting file from local, retry after 30s".format(status))
                    time.sleep(30)
                    attempt += 1
            else:
                if attempt < 5:
                    print("Instance not ready, retry after 30s...")
                    time.sleep(30)
                    attempt += 1
                    if self.instance:
                        self.instance.update()
                else:
                    raise RuntimeError("put file from local fails, instance may not launch.")


    def get_file_to_local(self, src, dst):
        attempt = 0
        while True:
            if self.instance and self.instance.public_dns_name:
                args = ['scp']
                args += ['-i', self.inst_key_file]
                args += ['-o', 'StrictHostKeyChecking=no']
                args += ['-o', 'UserKnownHostsFile=/dev/null']
                args += ['%s@%s:' % (self.inst_user_name, self.instance.public_dns_name) +
                        src]
                args += [dst]

                with open(os.devnull, 'w') as FNULL:
                    proc = subprocess.Popen(args, stdout = FNULL, stderr = subprocess.STDOUT)
                    status = proc.wait()


                if status == 0:
                    break
                elif attempt >= 5:
                    raise RuntimeError("get file to local fails with error %s" %
                            proc.returncode)
                else:
                    print("Error {0} while getting file to local, retry after 30s".format(status))
                    time.sleep(30)
                    attempt += 1
            else:
                if attempt < 5:
                    print("Instance not ready, retry after 30s...")
                    time.sleep(30)
                    attempt += 1
                    if self.instance:
                        self.instance.update()
                else:
                    raise RuntimeError("get file to local fails, instance may not launch.")

    def is_ssh_available(self):
        args = ['ssh']
        args += ['-i', self.inst_key_file]
        args += ['-t', '-t']
        args += ['-o', 'StrictHostKeyChecking=no']
        args += ['-o', 'UserKnownHostsFile=/dev/null']
        args += ['%s@%s' % (self.inst_user_name, self.instance.public_dns_name)]
        args += ['echo hello']

        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        retcode = proc.wait()

        return retcode == 0

    def update_proc_stats(self):
        for name,proc in self.processes.iteritems():
            if not proc.poll():
                self.processes.pop(name)

    def run_command(self, command, name = None):

        if not self.instance:
            print("Cannot run command because no instance launched.")
            sys.exit(1)

        while self.instance.update() != 'running':
            if self.instance.update() == 'terminated':
                print ('The instance %s has terminated.' % self.instance.id)
                sys.exit(0)
            print('The instance is %s, sleep 45s...' % self.instance.state)
            time.sleep(45)

        while not self.is_ssh_available():
            print('waiting for ssh available...')
            time.sleep(10)

        # build ssh command
        args = ['ssh']
        args += ['-i', self.inst_key_file]
        args += ['-t', '-t']
        args += ['-o', 'StrictHostKeyChecking=no']
        args += ['-o', 'UserKnownHostsFile=/dev/null']
        args += ['%s@%s' % (self.inst_user_name, self.instance.public_dns_name)]
        args += [command]

        with open(os.devnull, 'w') as FNULL:
            proc = subprocess.Popen(args, stdout = FNULL, stderr = subprocess.STDOUT)

        if name:
            assert(name not in self.processes)
            self.processes[name] = proc
        else:
            self.processes['default-' + str(len(self.processes))] = proc


