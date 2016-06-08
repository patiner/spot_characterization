# controller.py
# This script will launch instances and running avrora benchmark on them automatically
# To use, you need to setup your ec2_access_id and ec2_access_key in vm.py, the number
# of instance you want to run and traces, lb, es filename in the configuration field below

# This script will record the execution time of each job, usage of spot and OD instance in
# corresponding txt files


import re
import vm
import os
import sys
import math
import datetime
import logging
import json
import socket
import boto.ec2
import threading
import pdb

from time import sleep
from random import randint


logging.basicConfig(filename='spot_fail.log', format='%(asctime)s: %(message)s')

LOW_WEIGHT = 256
HIGH_WEIGHT = 1024
RHO = 1
K = 4
EC2_AMI = 'ami-75636f1f'
BID = 0.266
OD_price = 0.266
HOUR_INTERVAL = 300
MINUTE_INTERVAL = 5
NUM_CORE = 4
LONG_JOB_LENGTH = 100
JOB_LENGTH_SCALAR = 8
TRACE_LENGTH = 1440


def send_to_server(server_ip, data, port=10086):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))
    res_data = []

    try:
        sock.sendall(data)
        while True:
            res = sock.recv(1024)

            if res:
                res_data.append(res)
            else:
                break
    finally:
        sock.close()

    return ''.join(res_data)


def isServerAlive(server_ip, active_server_list):
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((server_ip, 22))
        return True
    except socket.error as e:
        return False
    """
    if not server_ip:
        return False

    for server in active_server_list:
        if server.ip == server_ip:
            return True

    return False


def launch_vm(v):
    v.launch_instance()


def get_vm(num_spot, num_backup):
    spot_list = []
    backup_list = []
    t = []

    for i in range(num_spot):
        new_vm = vm.VM(EC2_AMI,
                      'ec2-sample-key',
                      'ec2-sample-key.pem',
                      'ubuntu',
                      bidding = 1,
                      instance_type = 'c4.xlarge')

        spot_list.append(new_vm)
        t.append(threading.Thread(target = launch_vm, args = (new_vm,)))

    for i in range(num_backup):
        new_vm = vm.VM(EC2_AMI,
                      'ec2-sample-key',
                      'ec2-sample-key.pem',
                      'ubuntu',
                      bidding = 1,
                      instance_type = 'c4.xlarge')

        backup_list.append(new_vm)
        t.append(threading.Thread(target = launch_vm, args = (new_vm,)))

    for thread in t:
        thread.start()

    for thread in t:
        thread.join()

    return spot_list, backup_list


def add_job(running_jobs, spot_market_list, backup_market, time, job_length, job_id):
    global MINUTE_INTERVAL
    global JOB_LENGTH_SCALAR

    # ============================== Find the best market ==================================

    # find the index of trace
    trace_index = min(time / MINUTE_INTERVAL, TRACE_LENGTH - 1)

    # find feasible markets (Lb > job length)
    feasible_market = []
    candidate_market_count = 2

    for market in spot_market_list:
        # if remaining time > job length
        if market.Lb[trace_index] * MINUTE_INTERVAL > job_length * JOB_LENGTH_SCALAR:
            feasible_market.append(market)

    # if no feasible market, exit
    if not feasible_market:
        logging.error("No feasible market...")
        sys.exit(1)

    # find the smallest Esb market
    feasible_market = sorted(feasible_market, key = lambda market: market.Esb)
    chosen_market = feasible_market[randint(0, min(candidate_market_count, len(feasible_market)) - 1)]

    # ============================== Find open slot ========================================
    open_s_server = None
    open_b_server = None
    s_slot = None
    b_slot = None

    # find spot slot
    if chosen_market.spot_price[trace_index] > chosen_market.bid:
        print ('Price %f too high, job will not run on spot instances...' % chosen_market.spot_price[trace_index])
    else:
        for AS in chosen_market.active_list:
            # if remaining time > job length
            if (AS.Lb - (time - AS.created_time)) > job_length * JOB_LENGTH_SCALAR:
                s_slot = AS.find_open_slot()
                if s_slot:
                    open_s_server = AS
                    break

        # get new instances
        if not s_slot:
            print ('No slot available, get more instances...')
            open_s_server,s_slot = chosen_market.add_instance(time)
            print ('Now, %d free spot instance left...' % len(chosen_market.free_list))

    # find backup slot
    min_coef = sys.maxint
    for AB in backup_market.active_list:
        # b_slot = AB.find_open_slot()
        # if b_slot:
        #     open_b_server = AB
        #     break

        slot,coef = AB.find_open_slot_backup(chosen_market.name, chosen_market.bid, running_jobs)
        if slot and coef < min_coef:
            b_slot = slot
            min_coef = coef
            open_b_server = AB

    # get new instances
    if not b_slot:
        print ('No backup slot available, get more...')
        open_b_server,b_slot = backup_market.add_instance(time)
        print ('Now, %d free backup instance left...' % len(free_backup_list))

    # ================================ Run job ============================================
    if open_s_server:
        new_job = Job(open_s_server.ip, open_b_server.ip, s_slot, b_slot, 'avrora:v1', './start-up.sh %d' % job_length,
                      chosen_market.active_list, job_length, job_id, chosen_market.name, chosen_market.bid)
    else:
        new_job = Job(None, open_b_server.ip, s_slot, b_slot,'avrora:v1', './start-up.sh %d' % job_length,
                      chosen_market.active_list, job_length, job_id, chosen_market.name, chosen_market.bid)

    new_job.run(start_time=time)
    running_jobs.append(new_job)



def write_record(filename, count, cost):
    with open(filename, 'a') as f:
        f.write('%d     %f\n' % (count ,cost))



class Job:
    """ A class contain information about a job"""
    finished = False
    complete_time = 0

    def __init__(self, spot_ip, backup_ip, spot_cpuset, backup_cpuset, image, cmd, active_list, job_length, job_id,
                 market_name, bid):
        """ set instance ips and command for the job """
        self.spot_ip = spot_ip
        self.spot_cpuset = spot_cpuset
        self.backup_ip = backup_ip
        self.backup_cpuset = backup_cpuset
        self.image = image
        self.command = cmd
        self.active_list = active_list
        self.spot_fail = False
        self.spot_cid = None
        self.backup_cid = None
        self.job_length = job_length
        self.id = str(job_id)
        self.market_name = market_name
        self.bid = bid

    def run(self, start_time, spot_cpushares = HIGH_WEIGHT, backup_cpushares = LOW_WEIGHT):
        """ run a job on both spot and backup instances """
        try:
            cmd_to_spot = 'run$' + self.image + '|' +self.command + '|' + str(self.spot_cpuset) + '|' + str(spot_cpushares)
            cmd_to_backup = 'run$' + self.image + '|' +self.command + '|' + str(self.backup_cpuset) + '|' + str(backup_cpushares)
        except:
            print (self.image, self.command, self.spot_cpuset, spot_cpushares)
            sys.exit(1)

        if self.spot_ip:
            self.spot_cid = send_to_server(self.spot_ip, cmd_to_spot).strip()
        else:
            self.spot_fail = True

        self.backup_cid = send_to_server(self.backup_ip, cmd_to_backup).strip()
        self.start_time = start_time
        self.backup_cpushares = backup_cpushares



    def set_backup_cpushares(self, cpu_shares):
        print('setting cpu shares for %s to %d' % (self.backup_cid, cpu_shares))
        cmd = 'setcpu$' + self.backup_cid + '|' + str(cpu_shares)
        send_to_server(self.backup_ip, cmd)
        self.backup_cpushares = cpu_shares
        print ('Done')


    def update(self, current_time):
        """ check if a job is finished if it finishes on spot server
            terminate the copy on backup server and compute the finish time
        """

        if not self.spot_fail:
            print ('Checking job status on spot server...')
            cmd = 'inspect$' + self.spot_cid
            res = send_to_server(self.spot_ip, cmd)

            try:
                stat = json.loads(res)[0]
            except:
                print res
                print self.spot_cid
                print self.backup_cid
                print self.command

            if stat['state']['Status'] == 'exited' and stat['state']['ExitCode'] == 0:
                self.finished = True

                try:
                    start = datetime.datetime.strptime(stat['state']['StartedAt'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                    end = datetime.datetime.strptime(stat['state']['FinishedAt'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                except:
                    start = datetime.datetime.strptime(stat['state']['StartedAt'][:26], '%Y-%m-%dT%H:%M:%S.%fZ')
                    end = datetime.datetime.strptime(stat['state']['FinishedAt'][:26], '%Y-%m-%dT%H:%M:%S.%fZ')

                delta = end - start
                self.complete_time = delta.seconds
                #self.complete_time = current_time - self.start_time
                print ('The job %s/%s is finished on spot. Finished time is %f seconds' % (self.spot_cid, self.backup_cid, self.complete_time))

                # terminate the job on backup server
                print 'terminating the copy on backup server...',
                terminate_cmd = 'stop$' + self.backup_cid
                send_to_server(self.backup_ip, terminate_cmd)
                print 'Done.'

            if not isServerAlive(self.spot_ip, self.active_list):
                self.spot_fail = True

        else:
            print ('Spot server fails, checking job status on backup server...')
            cmd = 'inspect$' + self.backup_cid

            for i in range(5):
                try:
                    res = send_to_server(self.backup_ip, cmd)
                    stat = json.loads(res)[0]
                    break
                except:
                    logging.warning(res)
                    sleep(1)
                    continue

            if stat['state']['Status'] == 'exited' and stat['state']['ExitCode'] == 0:
                self.finished = True

                try:
                    start = datetime.datetime.strptime(stat['state']['StartedAt'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                    end = datetime.datetime.strptime(stat['state']['FinishedAt'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                except:
                    start = datetime.datetime.strptime(stat['state']['StartedAt'][:26], '%Y-%m-%dT%H:%M:%S.%fZ')
                    end = datetime.datetime.strptime(stat['state']['FinishedAt'][:26], '%Y-%m-%dT%H:%M:%S.%fZ')

                delta = end - start
                self.complete_time = delta.seconds
                # self.complete_time = current_time - self.start_time
                print ('The job %s/%s is finished on backup. Finished time is %f minutes' % (str(self.spot_cid), self.backup_cid, self.complete_time))

            elif stat['cpu_shares'] < HIGH_WEIGHT:
                self.set_backup_cpushares(HIGH_WEIGHT)



class Instance:
    """ A class store information about an EC2 instance """

    def __init__(self, ip, is_spot, num_core, Lb = None, Es = None, instance = None, bid = None):
        self.ip = ip
        self.is_spot = is_spot
        self.num_core = num_core
        self.Lb = Lb
        self.Es = Es
        self.instance = instance
        self.bid = bid
        self.created_time = None


    def report(self):
        """ report processes info """
        print ('IP: %s' % self.ip)
        if self.is_spot:
            print ('bid: %f' % self.bid)
        print ('%15s   %10s     %8s     %7s\n' % ('ID', 'CPU shares', 'CPU sets', 'Status'))
        get_stat_cmd = 'stat$'
        res = send_to_server(self.ip, get_stat_cmd)
        stat = json.loads(res)

        for s in stat:
            print ('%15s    %10s    %8s     %7s\n' % (s['id'], str(s['cpu_shares']), s['cpuset_cpus'].strip(), s['state']['Status']))

    def is_idle(self):
        get_stat_cmd = 'stat$'
        res = send_to_server(self.ip, get_stat_cmd)
        stat = json.loads(res)

        if not stat:
            return True
        else:
            return False



    def stop_all(self):
        """ stop all containers on the server """
        # stop all running job on the server
        cmd = 'stat$'
        res = send_to_server(self.ip, cmd)

        stat = json.loads(res)
        ids = []

        for s in stat:
            ids.append(s['id'])

        cmd = 'stop$' + '|'.join(ids)
        res = send_to_server(self.ip, cmd)



    def find_open_slot(self):
        """ return a cpuset number if available for a job """
        job_count = {}
        for i in range(self.num_core):
            job_count[i] = 0

        get_stat_cmd = 'stat$'
        res = send_to_server(self.ip, get_stat_cmd)
        try:
            stat = json.loads(res)
        except:
            print res

        for s in stat:
            # NOTE: cpuset_cpus must state in format 0,1,2,3,4... etc
            # The format such as 0-4 is not supported yet
            for core in s['cpuset_cpus'].strip().split(','):
                if core:
                    job_count[int(core)] += 1

        core_min = None
        min_job = sys.maxint    # some large number
        if self.is_spot:
            for c in range(self.num_core):
                if (job_count[c] < RHO and job_count[c] < min_job):
                    core_min = c
                    min_job = job_count[c]

        else:
            for c in range(self.num_core):
                if (job_count[c] < K * RHO and job_count[c] < min_job):
                    core_min = c
                    min_job = job_count[c]

        if core_min != None:
            return str(core_min)
        else:
            return None

    def find_open_slot_backup(self, market_name, bid, running_jobs):
        """ return a cpuset number if available for a job """
        job_count = {}
        coef_count = {}
        for i in range(self.num_core):
            job_count[i] = 0
            coef_count[i] = 0

        get_stat_cmd = 'stat$'
        res = send_to_server(self.ip, get_stat_cmd)
        try:
            stat = json.loads(res)
        except:
            print res

        for s in stat:
            # NOTE: cpuset_cpus must state in format 0,1,2,3,4... etc
            # The format such as 0-4 is not supported yet
            for core in s['cpuset_cpus'].strip().split(','):
                if core:
                    job_count[int(core)] += 1

                    for j in running_jobs:
                        if s['id'] == j.backup_cid:
                            if j.spot_fail:
                                coef_count[int(core)] += 1
                            else:
                                if market_name == j.market_name and bid == j.bid:
                                    coef_count[int(core)] += 1
                            break


        core_min = None
        min_coef = sys.maxint  # some large number

        # if self.is_spot:
        #     for c in range(self.num_core):
        #         if (job_count[c] < RHO and job_count[c] < min_job):
        #             core_min = c
        #             min_job = job_count[c]
        #
        # else:

        for c in range(self.num_core):
             if (job_count[c] < K * RHO and job_count[c] < min_coef):
                 core_min = c
                 min_coef = coef_count[c]

        if core_min != None and min_coef <= 1:
            return str(core_min),min_coef
        else:
            return None,min_coef


class ec2Market:
    def __init__(self, name, instance_type, free_list, bid = None, Lb = None, Esb = None, spot_price = None):
        self.name = name
        self.instance_type = instance_type
        self.free_list = free_list
        self.active_list = []
        self.bid = bid
        self.Lb = Lb
        self.Esb = Esb
        self.spot_price = spot_price

    def add_instance(self, time):
        if self.free_list:
            open_server = self.free_list.pop()
            open_slot = open_server.find_open_slot()

            open_server.bid = self.bid
            open_server.created_time = time

            trace_index = min(time / MINUTE_INTERVAL, TRACE_LENGTH - 1)

            if self.Lb:
                open_server.Lb = self.Lb[trace_index]
            if self.Esb:
                open_server.Es = self.Esb[trace_index]

            self.active_list.append(open_server)
        else:
            print ('No free instance available...')
            sys.exit(1)

        return (open_server, open_slot)

    def remove_active(self, time):
        """ Use to remove all active instances when spot market fails"""
        for server in self.active_list:
            server.stop_all()
            logging.warning('Spot server on market %s fails at time %d. Because spot price %f is larger than bid %f' %
                    (self.name, time, self.spot_price[min(time / MINUTE_INTERVAL, TRACE_LENGTH - 1)], self.bid))

            server.created_time = None
            server.spot_fail = False
            server.Lb = None
            server.Es = None
            server.bid = None
            self.free_list.append(server)
        del self.active_list[:]

    def check_spot_fail(self, time):
        if self.spot_price[min(time /MINUTE_INTERVAL, TRACE_LENGTH - 1)] > self.bid:
            self.remove_active(time)

    def status(self):
        print "=========================== %s =================================" % self.name
        print "Market type: %s" % self.instance_type
        for server in self.active_list:
            server.report()

    def remove_idles(self):
        idle_list = []
        for inst in self.active_list:
            if inst.is_idle():
                logging.warning('Instance %s is idle, removing it...' % inst.ip)
                idle_list.append(inst)

        for inst in idle_list:
            inst.created_time = None
            inst.Lb = None
            inst.Es = None
            inst.bid = None

            self.active_list.remove(inst)
            self.free_list.append(inst)


if __name__ == '__main__':

    # ==================================== Configuration =======================================
    spots, backups = get_vm(num_spot=10, num_backup=3)

    # get more time for initialization
    sleep(10)

    free_spot_list = []
    free_backup_list = []

    for s in spots:
        free_spot_list.append(Instance(s.instance.private_dns_name, True, NUM_CORE, instance = s.instance))

    for od in backups:
        free_backup_list.append(Instance(od.instance.private_dns_name, False, NUM_CORE, instance = od.instance))

    # Use for debug
    """
    free_spot_list = [Instance('54.209.193.99', True, 4),
                      Instance('54.175.247.52', True ,4),
                      Instance('54.174.223.12', True, 4),
                      Instance('54.175.19.187', True, 4),
                      Instance('52.91.253.90', True, 4)]

    free_backup_list = [Instance('54.209.178.139', False, 4),
                        Instance('54.88.47.178', False, 4)]
    """

    # read spot price trace
    with open('zone1/trace_1b.txt') as f:
        trace_1b = map(lambda x: float(x), f.readlines())

    with open('zone2/trace_1d.txt') as f:
        trace_1d = map(lambda x: float(x), f.readlines())

    trace_length = min(len(trace_1b), len(trace_1d))

    # read workload
    with open('workload.txt') as f:
        lines = f.readlines()
        workload = iter(lines)
        job_ids = iter(range(len(lines)))



    # read Lb
    with open('zone1/lb1_1b.txt') as f:
        lb1_1b = map(lambda x: float(x), f.readlines())

    with open('zone1/lb5_1b.txt') as f:
        lb5_1b = map(lambda x: float(x), f.readlines())

    with open('zone2/lb1_1d.txt') as f:
        lb1_1d = map(lambda x: float(x), f.readlines())

    with open('zone2/lb5_1d.txt') as f:
        lb5_1d = map(lambda x: float(x), f.readlines())

    # real Esb
    with open('zone1/es1_1b.txt') as f:
        es1_1b = map(lambda x: float(x), f.readlines())

    with open('zone1/es5_1b.txt') as f:
        es5_1b = map(lambda x: float(x), f.readlines())

    with open('zone2/es1_1d.txt') as f:
        es1_1d = map(lambda x: float(x), f.readlines())

    with open('zone2/es5_1d.txt') as f:
        es5_1d = map(lambda x: float(x), f.readlines())

    # create markets
    spot_market_list = [ec2Market('us-east-1b', 'spot', free_spot_list, bid=BID, Lb=lb1_1b, Esb=es1_1b, spot_price=trace_1b),
                        ec2Market('us-east-1b', 'spot', free_spot_list, bid=5*BID, Lb=lb5_1b, Esb=es5_1b, spot_price=trace_1b),
                        ec2Market('us-east-1d', 'spot', free_spot_list, bid=BID, Lb=lb1_1d, Esb=es1_1d, spot_price=trace_1d),
                        ec2Market('us-east-1d', 'spot', free_spot_list, bid=5*BID, Lb=lb5_1d, Esb=es5_1d, spot_price=trace_1d)]

    backup_market = ec2Market('On-Demand', 'OD', free_backup_list)

    # clear previous data
    if os.path.isfile('exec_time.txt'):
        os.remove('exec_time.txt')

    backup_filename = '%s.txt' % backup_market.name
    if os.path.isfile(backup_filename):
        os.remove(backup_filename)

    for market in spot_market_list:
        spot_filename = '%s_%f.txt' % (market.name, market.bid)
        if os.path.isfile(spot_filename):
            os.remove(spot_filename)

    # =================================== Running ============================================
    running_jobs = []
    finished_jobs = []
    hasJobs = True
    start = datetime.datetime.now()

    count = int((datetime.datetime.now() - start).seconds)
    try:
        next_job = map(lambda x: int(x), workload.next().strip().split())
    except StopIteration:
        print 'ERROR: Should have at least one job to start'
        sys.exit(1)

    while hasJobs:
        # next_job[0] is job length and next_job[1] is job arrival time
        while next_job and count >= next_job[1]:
            # add the job
            add_job(running_jobs, spot_market_list, backup_market, count, next_job[0], job_ids.next())

            # get the next job
            try:
                next_job = map(lambda x: int(x), workload.next().strip().split())
            except StopIteration:
                print 'No more jobs...'
                next_job = None
                hasJobs = False

        # if count % MINUTE_INTERVAL == 0:

        # check spot fail
        for market in spot_market_list:
            market.check_spot_fail(count)

        # check job finish
        for job in running_jobs:
            job.update(current_time=count)

            if job.finished:
                finished_jobs.append(job)
                with open('exec_time.txt', 'a') as f:
                    f.write('%s %f  %f\n' % (job.id, job.complete_time / MINUTE_INTERVAL, job.job_length))

        for job in finished_jobs:
            if job in running_jobs:
                running_jobs.remove(job)

        # record number of servers and cost
        for market in spot_market_list:
            write_record('%s_%f.txt' % (market.name, market.bid), len(market.active_list),
                         count)

        write_record('%s.txt' % backup_market.name, len(backup_market.active_list),
                     count)

        # close server if no jobs on it
        for market in spot_market_list:
            market.remove_idles()

        backup_market.remove_idles()

        # check server status
        for market in spot_market_list:
            market.status()

        backup_market.status()

        print 'Time: %d' % count

        count = int((datetime.datetime.now() - start).seconds)

    while running_jobs:
        print ('waiting job all done, %d jobs remain are still running...' % len(running_jobs))
        job_buf = []
        for job in running_jobs:
            job.update(current_time=count)

            if job.finished:
                finished_jobs.append(job)
                with open('exec_time.txt', 'a') as f:
                    f.write('%s %f  %f\n' % (job.id, job.complete_time / MINUTE_INTERVAL, job.job_length))

                job_buf.append(job)

        for job in job_buf:
            running_jobs.remove(job)

        # if count % MINUTE_INTERVAL == 0:

        # NOTE if the trace is long enough, we will use the trace
        # if not, we will use the last spot price available
        # if count / MINUTE_INTERVAL < trace_length:
        #    price_index = count / MINUTE_INTERVAL
        # else:
        #    price_index = trace_length - 1

        # record number of servers and cost
        for market in spot_market_list:
            write_record('%s_%f.txt' % (market.name, market.bid), len(market.active_list),
                         count)

        write_record('%s.txt' % backup_market.name, len(backup_market.active_list),
                     count)

        # close server if no jobs on it
        for market in spot_market_list:
            market.remove_idles()

        backup_market.remove_idles()

        # check server status
        for market in spot_market_list:
            market.status()

        backup_market.status()

        count = int((datetime.datetime.now() - start).seconds)

    for s in spots:
        s.terminate_instance()

    for od in backups:
        od.terminate_instance()
