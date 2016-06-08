# Simulate a three month trace
# Created by Qianlin Liang 3/30/2016

# change the configuration in main function and run

import sys
import os
import logging
import numpy as np

from uuid import uuid4
from random import randint

logging.basicConfig(filename='simulation.log', format='%(asctime)s: %(message)s')

def concurrent_fail(A, B, bid):

    if A and B:
        mat = np.corrcoef(A,B)
        return mat[0][1]
    elif not A and not B:
        return 1
    elif A and not B:
        return 1
    else:
        return 0

    # AorB = 0.0
    # AandB = 0.0
    #
    # if A and B:
    #     for i in range(len(A)):
    #         if A[i] > bid and B[i] > bid:
    #             AorB += 1
    #             AandB += 1
    #         elif A[i] > bid or B[i] > bid:
    #             AorB += 1
    #
    #     if AorB == 0:
    #         return 0
    #     else:
    #         return AandB / AorB
    #
    # elif A and not B:
    #     for i in range(len(A)):
    #         if A[i] > bid:
    #             AorB += 1
    #             AandB += 1
    #         else:
    #             AorB +=1
    #
    #     return AandB / AorB
    #
    # elif not A and B:
    #     for i in range(len(B)):
    #         if B[i] > bid:
    #             AorB += 1
    #             AandB += 1
    #         else:
    #             AorB += 1
    #
    #     return AandB / AorB
    #
    # else:
    #     return 1





class Core:

    def __init__(self, max_proc, is_spot):
        self.processes = {}
        self.max_proc = max_proc
        self.is_spot = is_spot

    def add_proc(self, proc, cpu_shares):
        if proc.id in self.processes:
            logging.error("process ID repeated")
            sys.exit(1)

        if self.is_spot:
            proc.spot_core = self
        else:
            proc.od_core = self

        self.processes[proc.id] = {'process': proc,
                                   'cpu_shares': cpu_shares}

    def has_proc(self, pid):
        return pid in self.processes

    def set_cpu_shares(self, pid, cpu_shares):
        if not self.has_proc(pid):
            logging.error("pid no found in this core")

        self.processes[pid]['cpu_shares'] = cpu_shares

    def run(self):
        cpu_share_sum = 0
        finished_job = []

        for proc in self.processes:
            cpu_share_sum += self.processes[proc]['cpu_shares']

        for proc in self.processes:
            if self.is_spot:
                self.processes[proc]['process'].spot_remain_time -= float(self.processes[proc]['cpu_shares']) / cpu_share_sum
            else:
                # if self.processes[proc]['cpu_shares'] == 1024:
                #     self.processes[proc]['process'].od_remain_time -= 1
                # else:
                self.processes[proc]['process'].od_remain_time -= float(self.processes[proc]['cpu_shares']) / cpu_share_sum

            if self.processes[proc]['process'].spot_remain_time < 0 or\
               self.processes[proc]['process'].od_remain_time < 0:
                finished_job.append(proc)

        for job in finished_job:
            self.processes[job]['process'].is_finish = True
            self.processes[job]['process'].od_core.stop_proc(job)
            if job in self.processes:
                del self.processes[job]

    def stop_proc(self, pid):
        del self.processes[pid]

    def proc_size(self):
        return len(self.processes)

    def is_idle(self):
        return len(self.processes) == 0

    def is_avalable(self):
        return len(self.processes) < self.max_proc

    def set_fail(self):
        for proc in self.processes:
            self.processes[proc]['process'].spot_fail = True
            self.processes[proc]['process'].od_core.set_cpu_shares(proc, 1024) #1024

    def coef(self, job, time):
        assert time >= 7*1440
        coef = 0.0
        if job.spot_trace:
            traceA = job.spot_trace[time-7*1440:time]
        else:
            traceA = None

        for proc in self.processes:
            if self.processes[proc]['process'].spot_trace:
                if traceA:
                    coef += concurrent_fail(traceA, self.processes[proc]['process'].spot_trace[time-7*1440:time],
                                            job.bid)
                else:
                    coef += concurrent_fail(traceA, self.processes[proc]['process'].spot_trace[time - 7 * 1440:time],
                                            self.processes[proc]['process'].bid)
            else:
                coef += concurrent_fail(traceA, None, job.bid)

        return coef

    def cofail(self):
        num_fail = 0
        for proc in self.processes:
            if self.processes[proc]['cpu_shares'] == 1024:
                num_fail += 1

        return num_fail




class Instance:

    def __init__(self, max_jobs, is_spot, num_core):
        self.cores = []

        for i in range(num_core):
            self.cores.append(Core(max_jobs / num_core, is_spot))

        self.max_jobs = max_jobs
        self.is_spot = is_spot

    def compute(self):
        for core in self.cores:
            core.run()

    def add_job(self, proc, cpu_shares=256, chosen_core=None):
        available_core = None

        if chosen_core:
            available_core = self.cores[chosen_core]
        else:
            for core in self.cores:
                if not available_core and core.is_avalable():
                    available_core = core

        available_core.add_proc(proc, cpu_shares)

    def is_idle(self):
        for core in self.cores:
            if not core.is_idle():
                return False

        return True

    def find_job(self, pid):
        for core in self.cores:
            if pid in core.processes:
                return core

        return None

    def job_count(self):
        job_sum = 0
        for core in self.cores:
            job_sum += len(core.processes)

        return job_sum

    def set_fail(self):
        for core in self.cores:
            core.set_fail()

    def report(self,time):
        total_cofail = 0.0
        for core in self.cores:
            total_cofail += core.cofail()

        with open("cofail.txt",'a') as f:
            f.write('%d     %f\n' % (time, total_cofail/4.0))


class Job:

    def __init__(self, length, time, job_id, spot_trace, bid):
        self.length = length
        self.od_remain_time = length
        self.spot_remain_time = length
        self.id = job_id
        self.created_time = time
        self.finish_time = None
        self.is_finish = False
        self.spot_fail = False
        self.spot_core = None
        self.od_core = None
        self.spot_trace = spot_trace
        self.bid = bid


class Market:

    def __init__(self, name, max_job, is_spot, lb=None, es=None, bid=None, spot_trace=None, num_core=4):
        self.name = name
        self.lb = lb
        self.es = es
        self.bid = bid
        self.spot_trace = spot_trace
        self.instance_list = []
        self.max_job = max_job
        self.is_spot = is_spot
        self.num_core = num_core

    def remove_active(self):
        for instance in self.instance_list:
            instance.set_fail()

        # empty the list
        del self.instance_list[:]

    def check_spot_fail(self, time):
        if self.spot_trace[min(time, len(self.spot_trace) - 1)] > self.bid:
            self.remove_active()

    def remove_idle(self):
        idle_list = []

        for instance in self.instance_list:
            if instance.is_idle():
                idle_list.append(instance)

        for instance in idle_list:
            self.instance_list.remove(instance)

    def find_available_instance(self):

        for instance in self.instance_list:
            if instance.job_count() < self.max_job:
                return instance

        new_instance = Instance(self.max_job, self.is_spot, self.num_core)
        self.instance_list.append(new_instance)
        return new_instance

    def find_backup_slot(self, job, time):
        candidates = []

        for instance in self.instance_list:
            if instance.job_count() < self.max_job:
                candidates.append(instance)

        if candidates:
            lowest_corelation = sys.maxint
            chosen_instance = None
            core_num = None

            if time < 7*1440:
                chosen_instance = candidates[0]
            else:
                for instance in candidates:
                    for j in range(len(instance.cores)):
                        core = instance.cores[j]
                        if core.proc_size() < core.max_proc:
                            coef = core.coef(job, time)
                            if coef < lowest_corelation:
                                lowest_corelation = coef
                                chosen_instance = instance
                                core_num = j

            if lowest_corelation <= 1 or time < 7*1440:
                return chosen_instance,core_num
            else:
                new_instance = Instance(self.max_job, self.is_spot, self.num_core)
                self.instance_list.append(new_instance)
                return new_instance, None

        else:
            new_instance = Instance(self.max_job, self.is_spot, self.num_core)
            self.instance_list.append(new_instance)
            return new_instance,0




    def process(self):
        for instance in self.instance_list:
            instance.compute()


def write_record(filename, count, cost):
    with open(filename, 'a') as f:
        f.write('%d     %f\n' % (count ,cost))


def main():
    pod = 0.266
    max_length = 129600
    max_job_backup = 4*4
    max_job_spot = 4
    lb_max_length = 119520
    high_weight = 1024

    # ============================= load data ================================

    # read spot price trace
    with open('zone1/trace_1b.txt') as f:
        trace_1b = map(lambda x: float(x.split()[0]), f.readlines())
        trace_1b = trace_1b[0:max_length]

    with open('zone2/trace_1d.txt') as f:
        trace_1d = map(lambda x: float(x.split()[0]), f.readlines())
        trace_1d = trace_1d[0:max_length]

    trace_length = min(len(trace_1b), len(trace_1d))

    # read workload
    with open('workload.txt') as f:
        lines = f.readlines()
        workload = iter(lines)
        job_ids = iter(range(len(lines)))

    # read Lb
    with open('zone1/lb1_1b.txt') as f:
        lb1_1b = map(lambda x: float(x), f.readlines())
        lb1_1b = lb1_1b[0:max_length]

    with open('zone1/lb5_1b.txt') as f:
        lb5_1b = map(lambda x: float(x), f.readlines())
        lb5_1b = lb5_1b[0:max_length]

    with open('zone2/lb1_1d.txt') as f:
        lb1_1d = map(lambda x: float(x), f.readlines())
        lb1_1d = lb1_1d[0:max_length]

    with open('zone2/lb5_1d.txt') as f:
        lb5_1d = map(lambda x: float(x), f.readlines())
        lb5_1d = lb5_1d[0:max_length]

    # real Esb
    with open('zone1/es1_1b.txt') as f:
        es1_1b = map(lambda x: float(x), f.readlines())
        es1_1b = es1_1b[0:max_length]

    with open('zone1/es5_1b.txt') as f:
        es5_1b = map(lambda x: float(x), f.readlines())
        es5_1b = es5_1b[0:max_length]

    with open('zone2/es1_1d.txt') as f:
        es1_1d = map(lambda x: float(x), f.readlines())
        es1_1d = es1_1d[0:max_length]

    with open('zone2/es5_1d.txt') as f:
        es5_1d = map(lambda x: float(x), f.readlines())
        es5_1d = es5_1d[0:max_length]

    spot_market_list = [Market('1b', max_job_spot, is_spot=True, lb=lb1_1b, es=es1_1b, bid=1*pod, spot_trace=trace_1b),
                        Market('1b', max_job_spot, is_spot=True, lb=lb5_1b, es=es5_1b, bid=5*pod, spot_trace=trace_1b),
                        Market('1d', max_job_spot, is_spot=True, lb=lb1_1d, es=es1_1d, bid=1*pod, spot_trace=trace_1d),
                        Market('1d', max_job_spot, is_spot=True, lb=lb5_1d, es=es5_1d, bid=5*pod, spot_trace=trace_1d)]

    backup_market = Market('On-Demand', max_job_backup, is_spot=False, num_core=4)

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

    if os.path.isfile('cofail.txt'):
        os.remove('cofail.txt')

    # =========================== Running ===============================
    running_jobs = []
    finished_jobs = []
    has_jobs = True
    time = 0

    try:
        next_job = map(lambda x: int(x), workload.next().strip().split())
    except StopIteration:
        print 'ERROR: Should have at least one job to start'
        sys.exit(1)

    while has_jobs:

        # next_job[0] is the arrival time of the job, next_job[1] is the job length
        # this is different from the origin controller
        while next_job and time >= next_job[0]:

            # =========================== find the best market ==============================
            trace_index = min(time, lb_max_length-1)

            feasible_market = []
            candidate_market_num = 2

            for market in spot_market_list:
                try:
                    if market.lb[trace_index] > next_job[1]:
                        feasible_market.append(market)
                except:
                    print(next_job)
                    print (len(market.lb))
                    sys.exit(1)

            if not feasible_market:
                # TODO: change this to use OD market only if no feasible market
                logging.warning('No feasible market...')
                chosen_market = None
            else:
                feasible_market = sorted(feasible_market, key=lambda market: market.es)
                chosen_market = feasible_market[randint(0, min(candidate_market_num, len(feasible_market)) - 1)]

            # =========================== add job ===================================
            # add to spot

            if chosen_market:
                new_job = Job(length=next_job[1], time=time, job_id=job_ids.next(), spot_trace=chosen_market.spot_trace,
                              bid=chosen_market.bid)
                target_spot_instance = chosen_market.find_available_instance()
                target_spot_instance.add_job(proc=new_job, cpu_shares=1024) # 1024
            else:
                new_job = Job(length=next_job[1], time=time, job_id=job_ids.next(), spot_trace=None, bid=None)

            # add to on backup
            # target_backup_instance,core = backup_market.find_backup_slot(new_job, time)
            target_backup_instance = backup_market.find_available_instance()
            core = None
            if chosen_market:
                target_backup_instance.add_job(new_job, cpu_shares=256, chosen_core=core)
            else:
                target_backup_instance.add_job(new_job, cpu_shares=1024, chosen_core=core) # 1024

            running_jobs.append(new_job)

            # get next job
            try:
                next_job = map(lambda x: int(x), workload.next().strip().split())
            except StopIteration:
                print 'No more jobs...'
                next_job = None
                has_jobs = False

        # simulate computing
        for market in spot_market_list:
            market.process()

        backup_market.process()

        # check spot failure
        for market in spot_market_list:
            market.check_spot_fail(time)

        # check job finish
        job_buf = []
        for job in running_jobs:

            if job.is_finish:
                job.finish_time = time - job.created_time
                finished_jobs.append(job)
                with open('exec_time.txt', 'a') as f:
                    f.write('%s %f  %f\n' % (job.id, job.finish_time, job.length))

                job_buf.append(job)

        for job in job_buf:
            running_jobs.remove(job)

        # record number of servers and cost
        for market in spot_market_list:
            write_record('%s_%f.txt' % (market.name, market.bid), len(market.instance_list), time)

        write_record('%s.txt' % backup_market.name, len(backup_market.instance_list), time)

        for market in spot_market_list:
            market.remove_idle()

        backup_market.remove_idle()

        print time
        print "Running Job: %d" % len(running_jobs)
        print "Finished Job: %d" % len(finished_jobs)
        print "OD size: %d" % len(backup_market.instance_list)

        if backup_market.instance_list:
            backup_market.instance_list[0].report(time)
        time += 1

    while running_jobs:
        # simulate computing
        for market in spot_market_list:
            market.process()

        backup_market.process()

        job_buf = []
        for job in running_jobs:
            if job.is_finish:
                job.finish_time = time - job.created_time
                finished_jobs.append(job)
                with open('exec_time.txt', 'a') as f:
                    f.write('%s %f  %f\n' % (job.id, job.finish_time, job.length))

                job_buf.append(job)

        for job in job_buf:
            running_jobs.remove(job)

        # record number of servers and cost
        for market in spot_market_list:
            write_record('%s_%f.txt' % (market.name, market.bid), len(market.instance_list), time)

        write_record('%s.txt' % backup_market.name, len(backup_market.instance_list), time)

        for market in spot_market_list:
            market.remove_idle()

        backup_market.remove_idle()

        print time
        if backup_market.instance_list:
            backup_market.instance_list[0].report(time)
        time += 1

if __name__ == '__main__':
    main()




