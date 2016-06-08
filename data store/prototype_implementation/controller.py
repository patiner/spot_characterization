#import vm
import socket
import math
import json
import threading
import time
from settings import *
import pdb
import copy

T_DELTA = 1000
T_DELTA_curr = 0
tp_request = False
tr_request = False
t_timer = None
tp_timer = None
tr_timer = None
T_INTERVAL = 90
TP_INTERVAL = 300
TR_INTERVAL = 60000
T_PRICE_INTERVAL = 60
T_STATUS = 10
l_target = 700.0
cpu_high = 50
cpu_low = 20
miss_rate_high = 0.05
miss_rate_low = 0.007
c_delta_od = 0
c_delta_spot = 0
m_delta_od = 0
m_delta_spot = 0
bid = 0.175
bid_fail = False
scaling_up_vm_tr_timer = 0
scaling_up_vm_tr_delay = 10
scaling_up_vm = False
i_time = 0
spot_fail_timer1 = 0
spot_fail_timer2 = 0
spot_fail_timer3 = 0
spot_fail_timer4 = 0
spot_fail_delay = 24
spot_fail1 = False
spot_fail2 = False
spot_fail3 = False
spot_fail4 = False
spot_fail_interval = 4
extra_noise = False
noise_duration = 300
noise_timer = 0
latency_ycsb = 0

# Input filename
spot_trace1_filename = 'input/price_1.txt'
spot_trace2_filename = 'input/price_2.txt'
input_type1_filenmae = 'input/us_east_1c_1OD.txt'
input_type2_filename = 'input/us_east_1c_5OD.txt'
input_type3_filename = 'input/us_east_1d_1OD.txt'
input_type4_filename = 'input/us_east_1d_5OD.txt'
input_OD_filename = 'input/on_demand.txt'

# Bids
OD_price = 0.133 # for m3.large
type1_bid = OD_price
type2_bid = 5 * OD_price
type3_bid = OD_price
type4_bid = 5 * OD_price

# use for thread target function
def launch_vm(v):
    v.launch_instance()

def set_tp_request():
    global tp_request
    tp_request = True

def set_tr_request():
    global tr_request
    tr_request = True

def set_t_delta():
    global T_DELTA
    T_DELTA = 0

def start_tp_timer():
    global tp_timer
    tp_timer = threading.Timer(600, set_tp_request)
    tp_timer.start()

def start_tr_timer():
    global tr_timer
    tr_timer = threading.Timer(120, set_tr_request)
    tr_timer.start()

def start_t_timer():
    t_timer = threading.Timer(240, set_t_delta)
    t_timer.start()

def reset_tp_timer():
    tp_timer.cancel()
    global tp_request
    tp_request = False
    start_tp_timer()

def reset_tr_timer():
    tr_timer.cancel()
    global tr_request
    tr_request = False
    start_tr_timer()

def reset_t_timer():
    t_timer.cancel()
    global T_DELTA
    T_DELTA = 0
    start_t_timer()



"""def get_vm():
    ycsb_clients = []
    memcached_od_server = []
    memcached_spot_server = []
    t = []

    memcached_cmd = 'python /home/ubuntu/memcached_daemon.py'

    # configure instance for YCSB client
    for i in range(YCSB_SIZE):
        new_vm = vm.VM('ami-cdb2e1a8',
                    'ec2-sample-key',
                    'ec2-sample-key.pem',
                    'ubuntu',
                    instance_type = 'm3.large')

        ycsb_clients.append(new_vm)
        t.append(threading.Thread(target = launch_vm, args = (new_vm,), name = 'YCSB-%d' % i))

    # configure OD instance for memcached server
    for i in range(MEMCACHED_OD_SIZE):
        new_vm = vm.VM('ami-f73d6d92',
                    'ec2-sample-key',
                    'ec2-sample-key.pem',
                    'ubuntu',
                    instance_type = 'm3.large',
                    user_data = memcached_cmd)

        memcached_od_server.append(new_vm)
        t.append(threading.Thread(target = launch_vm, args = (new_vm,), name = 'memcached-od-%d' % i))

    # configure spot instance for memcached server
    for i in range(MEMCACHED_SPOT_SIZE):
        new_vm = vm.VM('ami-f73d6d92',
                    'ec2-sample-key',
                    'ec2-sample-key.pem',
                    'ubuntu',
                    instance_type = 'm3.large',
                    user_data = memcached_cmd)

        memcached_spot_server.append(new_vm)
        t.append(threading.Thread(target = launch_vm, args = (new_vm,), name = 'memcached-spot-%d' % i))

    # start all instances
    for thread in t:
        thread.start()

    for thread in t:
        thread.join()

    return {'YCSB' : ycsb_clients,
            'memcached_od' : memcached_od_server,
            'memcached_spot' : memcached_spot_server}
"""

def send_to_server(server_ip, cmd, port = 12345):
    print server_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))

    try:
        sock.sendall(cmd)
        data = sock.recv(1024)
        #print data
    finally:
        sock.close()

    return data

#################################################
def send_to_mem(server_ip, cmd, port = 5001):
    print server_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))

    try:
        sock.sendall(cmd)
        data = sock.recv(1024)
        #print data
    finally:
        sock.close()

    return data
#####################################################
def get_latencies(server_ip, port = 12345):
    cmd = 'get$servers'
    data = send_to_server(server_ip, cmd, port = port)
    #print data
    
    if data is not None:
        try:
            ret = json.loads(data)
            return ret
        except ValueError:
            print "ValueError when json.loads(data)---"
            print data
    else:
        return '0'

def get_tput(server_ip, port = 12345):
    cmd = 'get$tput'
    data = send_to_server(server_ip, cmd, port = port)
    if data:
        return data
    else:
        return '0,0'

# get ram, cpu information from memcached server
def get_all_info(server_ip, port = 12345):
    cmd = 'get:all'
    data = send_to_server(server_ip, cmd, port = port)
    try:
        ret = json.loads(data)
        return ret
    except ValueError:
        print "ValueError when json.loads(data)---"
        print data


def run_cmd(server_ip, cmd, port = 12345):
    cmd = 'run$%s' % cmd

    send_to_server(server_ip, cmd, port = port)

def run_cmd_mem(server_ip, cmd, port = 12345):
    cmd = 'run:%s' % cmd

    send_to_server(server_ip, cmd, port = port)

# set ram, cpu information to memcached server
def set_ram(server_ip, ram_size, port = 12345):
    cmd = 'set:ram:%d' % int(ram_size)
    # TODO not sure what it return, so cannot check if it is
    # set successfully
    send_to_server(server_ip, cmd, port = port)

# set the number of core use in the server
def set_core(server_ip, core_size, port = 12345):
    cmd = 'set:core:%d' % int(core_size)
    # TODO same as set_ram
    send_to_server(server_ip, cmd, port = port)

def set_weights(server_ip, config, port = 12345):
    cmd = 'set$weights$%s' % config
    send_to_server(server_ip, cmd, port = port)

def reset_memcached(server_ip, port = 12345):
    cmd = 'reset:all'
    # TODO same as set_ram
    send_to_server(server_ip, cmd, port = port)

def flush_memcached(server_ip, port = 12345):
    cmd = 'flush:all'
    send_to_server(server_ip, cmd, port = port)

def reset_mcrouter(server_ip, port = 12345):
    cmd = 'reset$all'
    send_to_server(server_ip, cmd, port = port)

# create a dictionary of memcached server
def create_server_info(instance_list):
    server_status = {}
    for instance in instance_list:
        server_status[instance] = { 'core' : 0,
                                    'ram' : 0,
                                    'hot_weight': 0,
                                    'cold_weight': 0,
                                    'latency': 0,
                                    'cpu_util' : 0,
                                    'miss_rate': 0,
                                    'turnover' : 0,
				                    'cmd_get' : 0,
                                    'load_factor' : 0,
                                    'tput': 0,
                                    'private_ip': None}
    return server_status

def set_mcrouter_config(memcached_list_od, memcached_list_spot, mcrouter_list, port = 11211):
    filename = 'mcrouter-config'
    path = '/home/ubuntu/mcrouter-install/install'
    config = {
            "pools":{ "A":{ "servers":[] },
                      "B":{ "servers":[] }
                    },
            "route": { "type" : "PrefixSelectorRoute",
                       "policies": {
                            "h": {"type" : "HashRoute",
                                  "children" : "Pool|A",
                                  "hash_func" : "WeightedCh3",
                                  "weights" : []},
                            "c": {"type" : "HashRoute",
                                  "children" : "Pool|B",
                                  "hash_func" : "WeightedCh3",
                                  "weights" : []},
                                       },
                       "wildcard": {"type" : "HashRoute",
                            "children" : "Pool|A",
                            "hash_func" : "WeightedCh3",
                            "weights" : []}
                     }
            }
    # add ip address and weights to the config
    for server in memcached_list_od:
        config['pools']['A']['servers'].append(server + ':%d' % port)
        config['pools']['B']['servers'].append(server + ':%d' % port)
        if memcached_list_od[server]['hot_weight'] < 0.0001:
            config['route']['policies']['h']['weights'].append(0)
            config['route']['wildcard']['weights'].append(0)
        else:
            config['route']['policies']['h']['weights'].append(memcached_list_od[server]['hot_weight'])
            config['route']['wildcard']['weights'].append(memcached_list_od[server]['hot_weight'])
        
        if memcached_list_od[server]['cold_weight'] < 0.0001:
            config['route']['policies']['c']['weights'].append(0)
        else:
            config['route']['policies']['c']['weights'].append(memcached_list_od[server]['cold_weight'])

    for server in memcached_list_spot:
        config['pools']['A']['servers'].append(server + ':%d' % port)
        config['pools']['B']['servers'].append(server + ':%d' % port)
        if memcached_list_spot[server]['hot_weight'] < 0.0001:
            config['route']['policies']['h']['weights'].append(0)
        else:
            config['route']['policies']['h']['weights'].append(memcached_list_spot[server]['hot_weight'])
        if memcached_list_spot[server]['cold_weight'] < 0.0001:
            config['route']['policies']['c']['weights'].append(0)       
        else:
            config['route']['policies']['c']['weights'].append(memcached_list_spot[server]['cold_weight'])

    # with open(filename, 'w') as f:
    #    f.write(json.dumps(config))

    for server in mcrouter_list:
        set_weights(server, json.dumps(config))

def get_ram_scaleup(server_list, M_MAX):
    available_servers = {}
    for server in server_list:
        if server_list[server]['ram'] - M_MAX < -0.1:
            available_servers[server] = server_list[server]
    return available_servers

def get_ram_scaledown(server_list, M_MIN):
    available_servers = {}
    for server in server_list:
        if server_list[server]['ram'] - M_MIN > 0.1:
            available_servers[server] = server_list[server]

    return available_servers

def get_core_scaleup(server_list, C_MAX):
    available_servers = {}
    for server in server_list:
        if server_list[server]['core'] - C_MAX < -0.1:
            available_servers[server] = server_list[server]
    return available_servers

def get_core_scaledown(server_list, C_MIN):
    available_servers = {}
    for server in server_list:
        if server_list[server]['core'] - C_MIN > 0.1:
            available_servers[server] = server_list[server]
    return available_servers

def get_active_servers(server_list):
    active_servers = {}
    for server in server_list:
        if server_list[server]['hot_weight'] != 0 or server_list[server]['cold_weight'] != 0:
            active_servers[server] = server_list[server]

    return active_servers

def get_idle_server(server_list):
    for server in server_list:
        if server_list[server]['hot_weight'] == 0 and \
           server_list[server]['cold_weight'] == 0 and \
           server_list[server]['ram'] == 0 and \
           server_list[server]['core'] == 0:
            return (server, server_list[server])

    return None

def update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers):
    # set ram
    for server in memcached_servers_od:
        set_ram(server, memcached_servers_od[server]['ram'])
    for server in memcached_servers_spot:
        set_ram(server, memcached_servers_spot[server]['ram'])

    # set core
    for server in memcached_servers_od:
        set_core(server, memcached_servers_od[server]['core'])
    for server in memcached_servers_spot:
        set_core(server, memcached_servers_spot[server]['core'])

    for server in memcached_servers_od:
        if memcached_servers_od[server]['core'] > 0:
            cmd = 'thread_count:%d' %  memcached_servers_od[server]['core']
            send_to_mem(server, cmd)
    for server in memcached_servers_spot:
        if memcached_servers_spot[server]['core'] > 0:
            cmd = 'thread_count:%d' %  memcached_servers_spot[server]['core']
            send_to_mem(server, cmd)

    # set weight
    set_mcrouter_config(memcached_servers_od, memcached_servers_spot, mcrouter_servers)

def update_server_noise(memcached_servers_od, memcached_servers_spot, mcrouter_servers_noise):
    set_mcrouter_config(memcached_servers_od, memcached_servers_spot, mcrouter_servers_noise)

'''
def adjust_delta(is_spot, M_MIN, M_MAX, C_MIN, C_MAX):
    global m_delta_od
    global m_delta_spot
    global c_delta_od
    global c_delta_spot
    if is_spot:
        c_delta = c_delta_spot
        m_delta = m_delta_spot
    else:
        c_delta = c_delta_od
        m_delta = m_delta_od

    if m_delta
'''

def mem_scale(server_list, M_MIN, M_MAX, C_MIN, is_spot, called_by_tr):
    global m_delta_spot
    global m_delta_od
    global c_delta_od
    global c_delta_spot
    global T_DELTA
    global T_DELTA_curr
    global bid_fail
    if is_spot:
        m_delta = m_delta_spot
    else:
        m_delta = m_delta_od
    c_delta = 0

    active_servers = get_active_servers(server_list)

    if m_delta > 0 :
        capable_servers = get_ram_scaleup(active_servers, M_MAX)

        while m_delta > 20 and len(capable_servers) > 0:
            remain = 0
            mem_temp = m_delta
            mem_size = float(sum(capable_servers[server]['ram'] for server in capable_servers))
            if mem_size == 0:
                print 'mem_size ==0 ------'
                print capable_servers
                print server_list
            for server in capable_servers:
                new_mem = math.ceil((capable_servers[server]['ram'] / mem_size)*mem_temp +
                        capable_servers[server]['ram'])
                if new_mem > M_MAX:
                    #remain += new_mem - M_MAX
                    m_delta -= M_MAX - capable_servers[server]['ram']
                    capable_servers[server]['ram'] = M_MAX
                else:
                    m_delta -= new_mem- capable_servers[server]['ram']
                    capable_servers[server]['ram'] = new_mem
                if m_delta <= 0:
                    break  
                T_DELTA_curr = 0
            #m_delta = remain

            # update the origin list
            for server in capable_servers:
                server_list[server] = capable_servers[server]

            capable_servers = get_ram_scaleup(capable_servers, M_MAX)

        if m_delta > 0:
            for server in server_list:
                if (m_delta > 0 and
                   server_list[server]['ram'] == 0 and
                   server_list[server]['core'] == 0 and
                   server_list[server]['hot_weight'] == 0 and
                   server_list[server]['cold_weight'] == 0):
                       if m_delta < M_MIN:
                           server_list[server]['ram'] = M_MIN
                           m_delta -= M_MIN
                       elif m_delta > M_MAX:
                           server_list[server]['ram'] = M_MAX
                           m_delta -= M_MAX
                       else:
                           server_list[server]['ram'] = m_delta
                           m_delta -= m_delta
                       T_DELTA_curr = 0
                       server_list[server]['core'] = C_MIN
                       c_delta_od -= server_list[server]['core']
                       # add new server
                       if called_by_tr:
                           global scaling_up_vm
                           scaling_up_vm = True

        if m_delta > 0:
	    for server in server_list:
	        print server_list[server]['ram'], server
            #raise RuntimeError("Error, not enough VMs")
            print 'Not enough VMs-------------'

    elif(m_delta < 0):
        if T_DELTA >= T_INTERVAL or (is_spot and bid_fail):
            capable_servers = get_ram_scaledown(active_servers, M_MIN)
            while m_delta < -20 and len(capable_servers) > 0:
                remain = 0
                mem_temp = m_delta
                mem_size = float(sum(capable_servers[server]['ram'] for server in capable_servers))
                for server in capable_servers:
                    new_mem = math.floor(capable_servers[server]['ram'] +
                            (capable_servers[server]['ram'] / mem_size)*mem_temp)
                    if (new_mem < M_MIN):
                        #remain += new_mem
                        #pdb.set_trace()
                        m_delta += capable_servers[server]['ram'] 
                        capable_servers[server]['ram'] = 0
                  
                        c_delta += capable_servers[server]['core']
                        capable_servers[server]['core'] = 0
                        capable_servers[server]['hot_weight'] = 0
                        capable_servers[server]['cold_weight'] = 0
                    else:
                        m_delta += capable_servers[server]['ram'] - new_mem
                        capable_servers[server]['ram'] = new_mem
                    if m_delta >= 0:
                        break
                    

                for server in capable_servers:
                    server_list[server] = capable_servers[server]

                capable_servers = get_ram_scaledown(capable_servers, M_MIN)
            
            #if m_delta > 0:
            #    if is_spot:
            #        m_delta_spot = m_delta
            #        mem_scale(server_list, M_MIN, M_MAX, C_MIN, True, called_by_tr)
            #    else:
            #        m_delta_od = m_delta
            #        mem_scale(server_list, M_MIN, M_MAX, C_MIN, False, called_by_tr)
            
            if m_delta < 0:
                if abs(m_delta) >= M_MIN:
                    for server in active_servers:
                        if abs(m_delta) >= M_MIN:
                            active_servers[server]['ram'] = 0

                            c_delta += active_servers[server]['core']
                            active_servers[server]['core'] = 0
                            active_servers[server]['hot_weight'] = 0
                            active_servers[server]['cold_weight'] = 0
                            m_delta += M_MIN

                for server in capable_servers:
                    server_list[server] = active_servers[server]
    if is_spot:
        c_delta_spot += c_delta
    else:
        c_delta_od += c_delta


# Find the k largest
def k_largest(server_list, k):
    #pdb.set_trace()
    key_list = []
    for server_ip in server_list:
        key_list.append(server_ip)

    # bubble sort
    for i in range(len(key_list)):
        max_ram = key_list[i]
        for j in range(i+1, len(key_list)):
            if server_list[key_list[j]]['core'] > server_list[max_ram]['core']:
                max_ram = key_list[j]
        #key_list[i], key_list[key_list.index(max_ram)] = max_ram, key_list[i]
        key_list[key_list.index(max_ram)] = key_list[i]
        key_list[i] = max_ram
    return key_list[k]


def cpu_scale(server_list, C_MIN, C_MAX, M_MIN, is_spot, called_by_tr):

    global c_delta_spot
    global c_delta_od

    if is_spot:
        c_delta = c_delta_spot
    else:
        c_delta = c_delta_od

    global bid_fail
    global T_DELTA_curr

    active_servers = get_active_servers(server_list)
    #pdb.set_trace()
    if c_delta > 0:
        global T_DELTA_curr
        T_DELTA_curr = 0
        capable_servers = get_core_scaleup(active_servers, C_MAX)
        core_size = sum(capable_servers[server]['core'] for server in capable_servers)

        if c_delta > len(capable_servers)*C_MAX - core_size:
            for server in capable_servers:
                capable_servers[server]['core'] = C_MAX
                T_DELTA_curr = 0
            c_delta = c_delta - (len(capable_servers)*C_MAX - core_size)

            for server in server_list:
                if (c_delta > 0 and
                   server_list[server]['ram'] == 0 and
                   server_list[server]['core'] == 0 and
                   server_list[server]['hot_weight'] == 0 and
                   server_list[server]['cold_weight'] == 0):

                       if c_delta < C_MIN:
                           server_list[server]['core'] = C_MIN
                           c_delta -= C_MIN
                       elif c_delta > C_MAX:
                           server_list[server]['core'] = C_MAX
                           c_delta -= C_MAX
                       else:
                           server_list[server]['core'] = c_delta
                           c_delta -= c_delta
                       T_DELTA_curr = 0
                       server_list[server]['ram'] = M_MIN
                       # add new server
                       if called_by_tr:
                           global scaling_up_vm
                           scaling_up_vm = True

            if c_delta > 0:
                #raise RuntimeError("Error, not enough VMs")
                print "Not enough VMs-------------------"
        else:
            while c_delta > 0:
                temp_capable_servers = copy.deepcopy(capable_servers)
                for i in range(len(capable_servers)):
                    if c_delta != 0:
                        capable_servers[k_largest(temp_capable_servers, len(capable_servers)-1-i)]['core'] += 1
                        c_delta -= 1
                        T_DELTA_curr = 0
                capable_servers = get_core_scaleup(capable_servers, C_MAX)

            for server in capable_servers:
                server_list[server] = active_servers[server]
    else:
        print "prepare to scale down---"
        if T_DELTA >= T_INTERVAL or (is_spot and bid_fail):
            capable_servers = get_core_scaledown(active_servers, C_MIN)
            print "c_delta=%d, len(capable server)=%d" % (c_delta, len(capable_servers))
            while c_delta < 0 and len(capable_servers) > 0:
                #pdb.set_trace()
                temp_capable_servers = copy.deepcopy(capable_servers)
            	for i in range(len(capable_servers)):
                    if c_delta != 0:
                    	#capable_servers[k_largest(capable_servers, len(capable_servers) - 1 - i)]['core'] -= 1
                        capable_servers[k_largest(temp_capable_servers, i)]['core'] -= 1
                    	c_delta += 1

            	capable_servers = get_core_scaledown(capable_servers, C_MIN)

            for server in capable_servers:
            	server_list[server] = active_servers[server]

def update_load_factor(server_list):   
    for server in server_list:
        if server_list[server]['core'] == 0:
            server_list[server]['load_factor'] = 0
        elif server_list[server]['core'] == 1:
            server_list[server]['load_factor'] = 1
        elif server_list[server]['core'] == 2:
            server_list[server]['load_factor'] = 2
        elif server_list[server]['core'] == 3:
            server_list[server]['load_factor'] = 2.7
        else:
            server_list[server]['load_factor'] = 3.5
    
    ram_sum = sum(server_list[server]['ram'] for server in server_list)
    load_factor_sum =  float(sum(server_list[server]['load_factor'] for server in server_list))
   
    if load_factor_sum > 0:
        for server in server_list:
            server_list[server]['ram'] = server_list[server]['load_factor']/load_factor_sum * ram_sum
   
def update_load_factor_peak(server_list):
    for server in server_list:
        if server_list[server]['core'] == 0:
            server_list[server]['load_factor'] = 0
        elif server_list[server]['core'] == 1:
            server_list[server]['load_factor'] = 1
        elif server_list[server]['core'] == 2:
            server_list[server]['load_factor'] = 1.6
        elif server_list[server]['core'] == 3:
            server_list[server]['load_factor'] = 2.7
        else:
            server_list[server]['load_factor'] = 3.5

    ram_sum = sum(server_list[server]['ram'] for server in server_list)
    load_factor_sum =  float(sum(server_list[server]['load_factor'] for server in server_list))

    if load_factor_sum > 0:
        for server in server_list:
            server_list[server]['ram'] = server_list[server]['load_factor']/load_factor_sum * ram_sum


def reset_capacity(server_list, server):

    if server_list[server]['hot_weight'] == 0 and server_list[server]['cold_weight'] == 0:
        server_list[server]['core'] = 0
        server_list[server]['ram'] = 0   


def weight_scale(memcached_servers_od, x_t, y_t):

    #update_load_factor(memcached_servers_od)
    #update_load_factor(memcached_servers_spot)

    m_od_sum = float(sum(memcached_servers_od[server]['ram'] for server in memcached_servers_od))

    for server in memcached_servers_od:
        if m_od_sum == 0:
            memcached_servers_od[server]['hot_weight'] = 0
            memcached_servers_od[server]['cold_weight'] = 0
        else:
            memcached_servers_od[server]['hot_weight'] = (memcached_servers_od[server]['ram']/m_od_sum)*(x_t)
            memcached_servers_od[server]['cold_weight'] = (memcached_servers_od[server]['ram']/m_od_sum)*(y_t)
        reset_capacity(memcached_servers_od, server)



def get_status(memcached_servers_od, memcached_servers_spot, mcrouter_servers):

    status_data_mc = {}
    N = 0
    for mc_server in mcrouter_servers:
        temp = get_latencies(mc_server)
        if temp is not '0': 
            status_data_mc[mc_server] = temp
            N += 1
        else:
            print "mcrouter %s might be wrong" % mc_server
    print 'available mcrouter %d' % N
    for mem_server in memcached_servers_od:
        latencies = 0
        for mc_server in mcrouter_servers:
            #latencies += float(get_latencies(mc_server)[mem_server+':11211'])
            if mc_server in status_data_mc:
                latencies += float(status_data_mc[mc_server][mem_server+':11211'])
        memcached_servers_od[mem_server]['latency'] = latencies / max(1,N) #len(mcrouter_servers)

    for mem_server in memcached_servers_spot:
        latencies = 0
        for mc_server in mcrouter_servers:
            if mc_server in status_data_mc:
                latencies += float(status_data_mc[mc_server][mem_server+':11211'])
            #latencies += float(get_latencies(mc_server)[mem_server+':11211'])
        memcached_servers_spot[mem_server]['latency'] = latencies / max(1,N) #len(mcrouter_servers)


    for mc_server in mcrouter_servers:
        tput = get_tput(mc_server)
        if tput.split(',')[0] > 0:
            mcrouter_servers[mc_server]['tput'] = float(tput.split(',')[0])
        if tput.split(',')[1] > 0:
            mcrouter_servers[mc_server]['latency'] = float(tput.split(',')[1])


    # for mem_server in memcached_servers_od:
        # status = get_all_info(mem_server)
        # # miss rate
        # if float(status['cmd_get']) == 0:
            # memcached_servers_od[mem_server]['miss_rate'] = 0
        # else:
            # memcached_servers_od[mem_server]['miss_rate'] = float(status['get_misses']) / float(status['cmd_get'])
        # # cpu util
        # if status['cpu_util'] > 0:
            # memcached_servers_od[mem_server]['cpu_util'] = float(status['cpu_util'])
        # memcached_servers_od[mem_server]['cmd_get'] = float(status['cmd_get'])
        # # turnover
        # memcached_servers_od[mem_server]['turnover'] = (float(status['evictions']) + float(status['cmd_set'])) / max(float(status['curr_items']),1.0)

    # for mem_server in memcached_servers_spot:
        # status = get_all_info(mem_server)
        # # miss rate
        # if float(status['cmd_get']) == 0:
            # memcached_servers_spot[mem_server]['miss_rate'] = 0
        # else:
            # memcached_servers_spot[mem_server]['miss_rate'] = float(status['get_misses']) / float(status['cmd_get'])
        # # cpu util
        # if status['cpu_util'] > 0:
            # memcached_servers_spot[mem_server]['cpu_util'] = float(status['cpu_util'])
	# memcached_servers_spot[mem_server]['cmd_get'] = float(status['cmd_get'])
        # # turnover
        # memcached_servers_spot[mem_server]['turnover'] = (float(status['evictions']) + float(status['cmd_set'])) / max(float(status['curr_items']),1.0)




def tr_control(server_list, C_MIN, C_MAX, M_MIN, M_MAX, is_spot):
    c_delta = 0
    m_delta = 0
    global T_DELTA_curr
    global latency_ycsb
    #pdb.set_trace()
    for server in server_list:
        if latency_ycsb > 1000:
            
            c_i = server_list[server]['core']
            if c_i < C_MAX:
                T_DELTA_curr = 0
            #if server_list[server]['cpu_util'] / c_i >= cpu_high or (server_list[server]['miss_rate'] < miss_rate_high and server_list[server]['latency'] > 400):
            if server_list[server]['latency'] > 450:
                if math.ceil(c_i*(1 + 0.4*((latency_ycsb - l_target)/l_target))) > C_MAX:
                    c_delta += math.ceil(c_i*(1 + 0.4*((latency_ycsb - l_target)/l_target)) - C_MAX)
                    server_list[server]['core'] = C_MAX
                else:
                    server_list[server]['core'] = math.ceil(c_i*(1 + 0.4*((latency_ycsb - l_target)/l_target)))

            if server_list[server]['miss_rate'] > miss_rate_high:
                temp = server_list[server]['ram']*(1 + 0.1*((latency_ycsb - l_target)/l_target))
                if temp > M_MAX:
                    m_delta += temp - M_MAX
                    server_list[server]['ram'] = M_MAX
                else:
                    server_list[server]['ram'] = temp
	    if server_list[server]['ram'] < M_MAX:
                T_DELTA_curr = 0

        if server_list[server]['latency'] < 400:
            if T_DELTA >= T_INTERVAL:
                c_i = server_list[server]['core']
                if server_list[server]['cpu_util'] / c_i < cpu_low:
                    temp = math.ceil(c_i*(1 + 1.0*((server_list[server]['latency'] - 400)/400)))
                    if temp < C_MIN:
                        c_delta += temp - C_MIN
                        server_list[server]['core'] = C_MIN
                    else:
                        server_list[server]['core'] = temp

        if latency_ycsb < l_target and server_list[server]['miss_rate'] < miss_rate_low:
            if T_DELTA >= T_INTERVAL:              
                temp = server_list[server]['ram']*(1 + 0.3*((server_list[server]['latency'] - l_target)/l_target))
                if server_list[server]['turnover'] > 0.1:
                    s_i = 0.02
                else:
                    s_i = 0.05

                temp *= 1 + s_i

                if temp < M_MIN:
                    m_delta += temp - M_MIN
                    server_list[server]['ram'] = M_MIN
                else:
                    server_list[server]['ram'] = temp

    global m_delta_od
    global m_delta_spot
    global c_delta_od
    global c_delta_spot

    if is_spot:
        m_delta_spot = m_delta
        c_delta_spot = c_delta
    else:
        m_delta_od = m_delta
        c_delta_od = c_delta

def kill_all(server_pool):
    for lists in server_pool:
        for server in lists:
            for proc in server.processes:
                proc.kill()
                proc.update_proc_stats()


def write_server_stats_to_file(index, server_list, name_prefix):
    for server in server_list:
        filename = './results/%s_%s' % (name_prefix, str(server))
        try:
            f = open(filename,"a+")
            core = server_list[server]['core']
            ram = server_list[server]['ram']
            cpu_util = server_list[server]['cpu_util']/max(1, core)
            latency = server_list[server]['latency']
            miss_rate = server_list[server]['miss_rate']
            turnover = server_list[server]['turnover']
            hot_weight = server_list[server]['hot_weight']
            cold_weight = server_list[server]['cold_weight']
            cmd_get = server_list[server]['cmd_get']
            temp = '%d\t%d\t%d\t%f\t%f\t%f\t%f\t%f\t%f\t%d\n' % (index, core, ram, cpu_util, latency, miss_rate, turnover, hot_weight, cold_weight, cmd_get)
            f.write(temp)
            f.close()
        except IOError as e:
            print "Cannot open file: %s" % e.strerror
            break

def load_OD_input(filename):
    with open(filename) as f:
        lines = f.readlines()

    input_data = []
    for l in lines:
        entries = l.strip().split()
        input_data.append({'core' : int(entries[0]),
                           'mem'  : int(float(entries[1]) * 1024),
                           'x'    : float(entries[2]),
                           'y'    : float(entries[3])})
    return input_data


def load_spot_input(filename):
    with open(filename) as f:
        lines = f.readlines()

    input_data = []
    for l in lines:
        entries = l.strip().split()
        input_data.append({'instance_num' : int(entries[0]),
                           'x'    : float(entries[1]),
                           'y'    : float(entries[2])})
    return input_data

def load_traces(filename):
    with open(filename) as f:
        lines = f.readlines()

    trace = []
    for l in lines:
        price_time_pair = l.strip().split('\t')
        trace.append(float(price_time_pair[0]))

    return trace

def spot_instance_scale(instance_group, spot_pool, input_data):
    delta = abs(len(instance_group) - input_data.get('instance_num'))
    # scale up
    if len(instance_group) < input_data.get('instance_num'):
        for i in range(delta):
            new_ip,new_inst = get_idle_server(spot_pool)
            assert(new_ip != None and new_inst != None)
            instance_group[new_ip] = new_inst
            instance_group[new_ip]['core'] = C_DEFAULT
            instance_group[new_ip]['ram'] = M_DEFAULT
    # scale down
    elif len(instance_group) > input_data.get('instance_num'):
        for i in range(delta):
            tmp_key = instance_group.keys()[0]
            instance_group[tmp_key]['core'] = 0
            instance_group[tmp_key]['ram'] = 0
            instance_group[tmp_key]['hot_weight'] = 0
            instance_group[tmp_key]['cold_weight'] = 0
            instance_group.pop(tmp_key)

    weight_scale(instance_group, input_data.get('x'), input_data.get('y'))


def weight_transfer(spot_group, OD_group, OD_data, spot_data, timer):
    global m_delta_od
    global c_delta_od
    global spot_fail_interval
    global spot_fail_delay
    global G_M_MIN
    global G_M_MAX
    global G_C_MIN
    global G_C_MAX

    spot_fail_timer = timer
    print 'spot_fail_timer = %d' % spot_fail_timer

    if spot_fail_timer % spot_fail_interval == 0:
        print 'move data'

        m_delta_od = float(math.ceil((spot_data.get('instance_num') * M_DEFAULT) / (spot_fail_delay / spot_fail_interval)))
        mem_scale(OD_group, G_M_MIN, G_M_MAX, G_C_MIN, False, True)

        if spot_fail_timer == 0:
            c_delta_od = spot_data.get('instance_num') * C_DEFAULT
            cpu_scale(OD_group, G_C_MIN, G_C_MAX, G_M_MIN, False, True)

        x_spot = sum(spot_group[spot].get('hot_weight') for spot in spot_group) - spot_data.get('x') / (spot_fail_delay / spot_fail_interval)
        y_spot = sum(spot_group[spot].get('cold_weight') for spot in spot_group) - spot_data.get('y') / (spot_fail_delay / spot_fail_interval)
        x_od = sum(OD_group[od].get('hot_weight') for od in OD_group) + spot_data.get('x') / (spot_fail_delay / spot_fail_interval)
        y_od = sum(OD_group[od].get('cold_weight') for od in OD_group) + spot_data.get('y') / (spot_fail_delay / spot_fail_interval)

        weight_scale(OD_group, x_od, y_od)
        weight_scale(spot_group, x_spot, y_spot)



#def main(server_pool):
def main():
    global T_DELTA
    global TP_INTERVAL
    global bid
    global bid_fail
    global TR_INTERVAL
    
    global T_DELTA_curr
    global m_delta_od
    global m_delta_spot
    global c_delta_od
    global c_delta_spot
    global i_time

    global scaling_up_vm
    global scaling_up_vm_tr_timer
    global scaling_up_vm_tr_delay

    global spot_fail
    global spot_fail_delay
    global spot_fail_timer
    global spot_fail_interval

    global noise_duration
    global noise_timer
    global extra_noise

    global latency_ycsb
    global spot_fail_timer1
    global spot_fail_timer2
    global spot_fail_timer3
    global spot_fail_timer4

    # get instances
    #server_pool = get_vm()

    mcrouter_list = []
    mcrouter_noise_list = []
    memcached_od_list = []
    memcached_spot_list = []

    with open("memcached_od_list.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            memcached_od_list.append(line.strip('\n'))
    print memcached_od_list

    with open("memcached_spot_list.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            memcached_spot_list.append(line.strip('\n'))
    print memcached_spot_list

    with open("mcrouter_list.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            mcrouter_list.append(line.strip('\n'))
    print mcrouter_list


    """
    with open("mcrouter_noise_list.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            mcrouter_noise_list.append(line.strip('\n'))
    """

    #print mcrouter_noise_list

    server_pool = {'memcached_od':memcached_od_list, 'memcached_spot':memcached_spot_list, 'YCSB': mcrouter_list, 'YCSB_noise': mcrouter_noise_list}
 
    

    # create dictionary info
    memcached_servers_od = create_server_info(server_pool['memcached_od'])
    memcached_servers_spot = create_server_info(server_pool['memcached_spot'])
    mcrouter_servers = create_server_info(server_pool['YCSB'])
    #cheng: adding noise via mcrouter_servers_noise
    mcrouter_servers_noise = create_server_info(server_pool['YCSB_noise'])


    # set mcrouter config
    set_mcrouter_config(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
    #set_mcrouter_config(memcached_servers_od, memcached_servers_spot, mcrouter_servers_noise)
    """
    # run memcached daemon
    mem_cmd = 'python memcached_daemon.py'
    for server in memcached_servers_od:
        memcached_servers_od[server]['instance'].run_command(mem_cmd)
    for server in memcached_servers_spot:
        memcached_servers_spot[server]['instance'].run_command(mem_cmd)

    # run mcrouter daemon
    mc_cmd = 'python mcrouter_daemon.py'
    for server in mcrouter_servers:
        mcrouter_servers[server]['instance'].run_command(mc_cmd)
    """

    #==================== Load inputs ======================
    # single market
    """with open('opt.txt', 'r') as f:
        lines = f.readlines()
        x_t = [float(line.split('\t')[0]) for line in lines]
        y_t = [float(line.split('\t')[1]) for line in lines]
        m_o = [1024*float(line.split('\t')[2]) for line in lines]
        m_s = [1024*float(line.split('\t')[3]) for line in lines]
        c_o = [float(line.split('\t')[4]) for line in lines]
        c_s = [float(line.split('\t')[5]) for line in lines]
    """

    # multi-market
    # spot trace
    spot_trace1 = load_traces(spot_trace1_filename)
    spot_trace2 = load_traces(spot_trace2_filename)

    # inputs
    type1_input = load_spot_input(input_type1_filenmae)
    type2_input = load_spot_input(input_type2_filename)
    type3_input = load_spot_input(input_type3_filename)
    type4_input = load_spot_input(input_type4_filename)
    OD_input = load_OD_input(input_OD_filename)



    with open('input/arrival_actual.txt', 'r') as f:
        lines = f.readlines()
        arrival = map(lambda x: 320000*float(x), lines)

    #arrival[9] = arrival[9] *325000/300000

    with open('random_seed.txt', 'r') as f:
        lines = f.readlines()
        random_seed = map(int, lines)
    

    with open('input/workingset_actual.txt', 'r') as f:
        lines = f.readlines()
        working_set = map(lambda x : int(15728640*float(x)), lines)

    """with open('spotprice_min.txt','r') as f:
        lines = f.readlines()
        spotprice_min = map(lambda x : float(x), lines)
    """

    # kill exist ycsb
    cmd = 'thread_count:2'

    for server in memcached_servers_od:
         send_to_mem(server, cmd)
    for server in memcached_servers_spot:
         send_to_mem(server, cmd)

    # kill exist ycsb
    cmd = 'killall java'

    for server in mcrouter_servers:
         run_cmd(server, cmd)

    #for server in mcrouter_servers_noise:
    #     run_cmd(server, cmd)

    time.sleep(2)
    tp = 5 * min(len(spot_trace1), len(spot_trace2))

    for i_time in range(tp):

        #if i_time > 10 and i_time < 13*TP_INTERVAL-10:
        #    continue


        #if i_time > 17*TP_INTERVAL+10 and i_time < 18*TP_INTERVAL-10:
        #   continue


        #if i_time > 18*TP_INTERVAL+10 and i_time < 19*TP_INTERVAL-10:
        #   continue

        #if i_time > 15*TP_INTERVAL-200:
        #    return

        if i_time == 0:
            n_o = int(math.ceil(max([OD_input[i_time].get('mem')/float(M_DEFAULT), OD_input[i_time].get('core')/float(C_DEFAULT)])))


            count = 0
            for server in memcached_servers_od:
                if (count < n_o and
                        memcached_servers_od[server]['ram'] == 0 and
                        memcached_servers_od[server]['core'] == 0 and
                        memcached_servers_od[server]['hot_weight'] == 0 and
                        memcached_servers_od[server]['cold_weight'] == 0):
                    memcached_servers_od[server]['ram'] = M_DEFAULT
                    memcached_servers_od[server]['core'] = C_DEFAULT
                    count += 1

            weight_scale(memcached_servers_od, OD_input[i_time].get('x'), OD_input[i_time].get('y'))

            """count = 0
            for server in memcached_servers_spot:
                if (count < n_s and
                        memcached_servers_spot[server]['ram'] == 0 and
                        memcached_servers_spot[server]['core'] == 0 and
                        memcached_servers_spot[server]['hot_weight'] == 0 and
                        memcached_servers_spot[server]['cold_weight'] == 0):
                    memcached_servers_spot[server]['ram'] = M_DEFAULT
                    memcached_servers_spot[server]['core'] = C_DEFAULT
                    count += 1
            """

            #=========================== Initializing 4 types of spot instances ======================
            type1_instances = {}
            type2_instances = {}
            type3_instances = {}
            type4_instances = {}

            for i in range(type1_input[i_time].get('instance_num')):
                tmp_ip,tmp_inst = get_idle_server(memcached_servers_spot)
                type1_instances[tmp_ip] = tmp_inst
                type1_instances[tmp_ip]['ram'] = M_DEFAULT
                type1_instances[tmp_ip]['core'] = C_DEFAULT

            weight_scale(type1_instances, type1_input[i_time].get('x'), type1_input[i_time].get('y'))

            for i in range(type2_input[i_time].get('instance_num')):
                tmp_ip,tmp_inst = get_idle_server(memcached_servers_spot)
                type2_instances[tmp_ip] = tmp_inst
                type2_instances[tmp_ip]['ram'] = M_DEFAULT
                type2_instances[tmp_ip]['core'] = C_DEFAULT

            weight_scale(type2_instances, type2_input[i_time].get('x'), type2_input[i_time].get('y'))

            for i in range(type3_input[i_time].get('instance_num')):
                tmp_ip,tmp_inst = get_idle_server(memcached_servers_spot)
                type3_instances[tmp_ip] = tmp_inst
                type3_instances[tmp_ip]['ram'] = M_DEFAULT
                type3_instances[tmp_ip]['core'] = C_DEFAULT

            weight_scale(type3_instances, type3_input[i_time].get('x'), type3_input[i_time].get('y'))

            for i in range(type4_input[i_time].get('instance_num')):
                tmp_ip,tmp_inst = get_idle_server(memcached_servers_spot)
                type4_instances[tmp_ip] = tmp_inst
                type4_instances[tmp_ip]['ram'] = M_DEFAULT
                type4_instances[tmp_ip]['core'] = C_DEFAULT

            weight_scale(type4_instances, type4_input[i_time].get('x'), type4_input[i_time].get('y'))



            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            #reset / flush the servers
            #for server in memcached_servers_od:
            #    reset_memcached(server)
            #   flush_memcached(server)
            #for server in memcached_servers_spot:
            #   reset_memcached(server)
            #   flush_memcached(server)

            cmd = 'killall java'

            for server in mcrouter_servers:
                run_cmd(server, cmd)


            cmd = 'sudo rm /home/ubuntu/ycsb/YCSB-master/stats'

            for server in mcrouter_servers:
                run_cmd(server, cmd)

            time. sleep(1)

            cmd = '/home/ubuntu/ycsb/YCSB-master/bin/ycsb run memcached -P ycsb/YCSB-master/workloads/workloadc\
            -p recordcount=%d -p maxexecutiontime=3600 -p hot_keys_file=/home/ubuntu/hot_keys_folder/hot_keys_2_%d\
            -p random_seed=%d -p memcached.server=localhost:11211 -p enable_key_count_hashmap=false\
            -p enable_key_popularity_stat=false -p enable_key_partition=true -threads 25\
            -target %d -s > ycsb/YCSB-master/stats 2>&1'\
                    % (working_set[0], 1, random_seed[0], int(math.ceil(arrival[0]/float(len(mcrouter_servers)))))

            for server in mcrouter_servers:
                run_cmd(server, cmd)

            time.sleep(300)

        elif i_time % TP_INTERVAL == 0:
            index = i_time / TP_INTERVAL
            #index = 8


            m_delta_od = OD_input[index].get('mem') - sum(memcached_servers_od[server]['ram'] for server in memcached_servers_od)
            c_delta_od = OD_input[index].get('core') - sum(memcached_servers_od[server]['core'] for server in memcached_servers_od)

            """
            m_delta_spot = m_s[index] - sum(memcached_servers_spot[server]['ram'] for server in memcached_servers_spot)
            c_delta_spot = c_s[index] - sum(memcached_servers_spot[server]['core'] for server in memcached_servers_spot)
            """

            # for OD first
            #adjust_delta(False, G_M_MIN, G_M_MAX, G_C_MIN, G_C_MAX)
            #adjust_delta(True, M_DEFAULT, M_DEFAULT, C_DEFAULT, C_DEFAULT)


            print 'm_o = %f' % OD_input[index].get('mem')
            print 'c_o = %f' % OD_input[index].get('core')
            print 'm_delta_o = %f' % m_delta_od
            print 'c_delta_o = %f' % c_delta_od


            T_DELTA_curr = T_DELTA
            # memory scale on-demand instance
            mem_scale(memcached_servers_od, G_M_MIN, G_M_MAX, G_C_MIN, False, False)

            # cpu scale on-demand instance
            cpu_scale(memcached_servers_od, G_C_MIN, G_C_MAX, G_M_MIN, False, False)

            # memory scale spot instance
            #mem_scale(memcached_servers_spot, M_DEFAULT, M_DEFAULT, C_DEFAULT, True, False)

            # cpu scale spot instance
            #cpu_scale(memcached_servers_spot, C_DEFAULT, C_DEFAULT, M_DEFAULT, True, False)

            #========================== Scale spot instances =====================
            spot_instance_scale(type1_instances, memcached_servers_spot, type1_input[index])
            spot_instance_scale(type2_instances, memcached_servers_spot, type2_input[index])
            spot_instance_scale(type3_instances, memcached_servers_spot, type3_input[index])
            spot_instance_scale(type4_instances, memcached_servers_spot, type4_input[index])

            if T_DELTA_curr == 0:
                T_DELTA = 0             

            # weight scale
            #update_load_factor(memcached_servers_od)
            #update_load_factor(memcached_servers_spot)


            #if i_time == 9*TP_INTERVAL:
            #    update_load_factor_peak(memcached_servers_od)
            #    update_load_factor_peak(memcached_servers_spot)

            #weight_scale(memcached_servers_od, memcached_servers_spot, x_t[index], y_t[index])
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            for server in memcached_servers_spot:
                reset_memcached(server)
            for server in memcached_servers_od:
                reset_memcached(server)

            # kill exist ycsb
            cmd = 'killall java'

            for server in mcrouter_servers:
                run_cmd(server, cmd)

            time.sleep(3)

            cmd = 'sudo rm /home/ubuntu/ycsb/YCSB-master/stats'

            for server in mcrouter_servers:
                run_cmd(server, cmd)

            time.sleep(1)

            # if index <= 19:
                # new_index = index + 8
            # else:
                # new_index = index -16
			new_index = index

            cmd = '/home/ubuntu/ycsb/YCSB-master/bin/ycsb run memcached -P ycsb/YCSB-master/workloads/workloadc\
            -p recordcount=%d -p maxexecutiontime=3600 -p hot_keys_file=/home/ubuntu/hot_keys_folder/hot_keys_2_%d\
            -p random_seed=%d -p memcached.server=localhost:11211 -p enable_key_count_hashmap=false\
            -p enable_key_popularity_stat=false -p enable_key_partition=true -threads 30\
            -target %d -s > ycsb/YCSB-master/stats 2>&1'\
            % (working_set[index], new_index, random_seed[index], int(math.ceil(arrival[index]/float(len(mcrouter_servers)))))

            for server in mcrouter_servers:
                run_cmd(server, cmd)

            print 'OD-------------'
            #print memcached_servers_od
            for server in memcached_servers_od:
                print memcached_servers_od[server]['core'], memcached_servers_od[server]['ram']
            #print 'SI---------------'
            #print memcached_servers_spot


            time.sleep(40)

        """
        elif i_time % TR_INTERVAL == 0: # and i_time >2*TP_INTERVAL:

            print "reactive control---"
            index = i_time / TP_INTERVAL
            #index = 8
            active_od = get_active_servers(memcached_servers_od)
            active_spot = get_active_servers(memcached_servers_spot)
            get_status(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            tr_control(active_od, G_C_MIN, G_C_MAX, G_M_MIN, G_M_MAX, False)
            tr_control(active_spot, C_DEFAULT, C_DEFAULT, M_DEFAULT, M_DEFAULT, True)

            T_DELTA_curr = T_DELTA
            # memory scale on-demand instance
            mem_scale(memcached_servers_od, G_M_MIN, G_M_MAX, G_C_MIN, False, True)
            # memory scale spot instance
            mem_scale(memcached_servers_spot, M_DEFAULT, M_DEFAULT, C_DEFAULT, True, True)

            # cpu scale on-demand instance
            cpu_scale(memcached_servers_od, G_C_MIN, G_C_MAX, G_M_MIN, False, True)
            # cpu scale spot instance
            cpu_scale(memcached_servers_spot, C_DEFAULT, C_DEFAULT, M_DEFAULT, True, True)

            if T_DELTA_curr == 0:
                T_DELTA = 0

            if scaling_up_vm:
                print 'scaling up vm == true'
            # weight scale
            #weight_scale(memcached_servers_od, memcached_servers_spot, x_t[index], y_t[index])
                update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
                scaling_up_vm_tr_timer += 1
                scaling_up_vm = False
            else:
                weight_scale(memcached_servers_od, memcached_servers_spot, x_t[index], y_t[index])
                update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            for server in memcached_servers_spot:
                reset_memcached(server)

            for server in memcached_servers_od:
                reset_memcached(server)


            #print 'OD-------------'
            #print memcached_servers_od
            #print 'SI---------------'
            #print memcached_servers_spot
        


        if scaling_up_vm_tr_timer > 0:
            scaling_up_vm_tr_timer += 1;
            print 'scaling up vm tr timer = %d' % scaling_up_vm_tr_timer
        if scaling_up_vm_tr_timer >= scaling_up_vm_tr_delay:
            print 'start to scaling up vm for reactive control'
            scaling_up_vm_tr_timer = 0
            index = i_time / TP_INTERVAL
            #index = 8
            weight_scale(memcached_servers_od, memcached_servers_spot, x_t[index], y_t[index])
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
        """
        
        
        # bid fails after 12 sec --> 120 sec in reality  --> change weight every 2 sec
        index = i_time / 5

        """
        if i_time == 14*TP_INTERVAL+4*TR_INTERVAL+24:
            index = i_time / TP_INTERVAL
            
            print 'spot fails after 2 min (12 sec)'
            spot_fail = True
            x = x_t[index]
            y = y_t[index]
            #spot_fail_timer += 1
        """

        spot_fail1 = type1_bid < spot_trace1[index]
        spot_fail2 = type2_bid < spot_trace1[index]
        spot_fail3 = type3_bid < spot_trace2[index]
        spot_fail4 = type4_bid < spot_trace2[index]

        if spot_fail1 and type1_instances:
            weight_transfer(type1_instances, memcached_servers_od, OD_input[i_time / 300], type1_input[i_time / 300], spot_fail_timer1)
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            spot_fail_timer1 = spot_fail_timer1 + 1
            if spot_fail_timer1 >= spot_fail_delay:
                for server in type1_instances:
                    type1_instances[server]['core'] = 0
                    type1_instances[server]['ram'] = 0
                    type1_instances[server]['hot_weight'] = 0
                    type1_instances[server]['cold_weight'] = 0
                    type1_instances[server]['cpu_util'] = 0
                    type1_instances[server]['latency'] = 0
                    type1_instances[server]['turnover'] = 0

                type1_instances = {}

                print 'spot instance terminated---'
                spot_fail_timer1 = 0

        if spot_fail2 and type2_instances:
            weight_transfer(type2_instances, memcached_servers_od, OD_input[i_time / 300], type2_input[i_time / 300], spot_fail_timer2)
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            spot_fail_timer2 = spot_fail_timer2 + 1
            if spot_fail_timer2 >= spot_fail_delay:
                for server in type2_instances:
                    type2_instances[server]['core'] = 0
                    type2_instances[server]['ram'] = 0
                    type2_instances[server]['hot_weight'] = 0
                    type2_instances[server]['cold_weight'] = 0
                    type2_instances[server]['cpu_util'] = 0
                    type2_instances[server]['latency'] = 0
                    type2_instances[server]['turnover'] = 0

                type2_instances = {}

                print 'spot instance terminated---'
                spot_fail_timer2 = 0

        if spot_fail3 and type3_instances:
            weight_transfer(type3_instances, memcached_servers_od, OD_input[i_time / 300], type3_input[i_time / 300], spot_fail_timer3)
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            spot_fail_timer3 = spot_fail_timer3 + 1
            if spot_fail_timer3 >= spot_fail_delay:
                for server in type3_instances:
                    type3_instances[server]['core'] = 0
                    type3_instances[server]['ram'] = 0
                    type3_instances[server]['hot_weight'] = 0
                    type3_instances[server]['cold_weight'] = 0
                    type3_instances[server]['cpu_util'] = 0
                    type3_instances[server]['latency'] = 0
                    type3_instances[server]['turnover'] = 0

                type3_instances = {}

                print 'spot instance terminated---'
                spot_fail_timer3 = 0

        if spot_fail4 and type4_instances:
            weight_transfer(type4_instances, memcached_servers_od, OD_input[i_time / 300], type4_input[i_time / 300], spot_fail_timer4)
            update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            spot_fail_timer4 = spot_fail_timer4 + 1
            if spot_fail_timer4 >= spot_fail_delay:
                for server in type4_instances:
                    type4_instances[server]['core'] = 0
                    type4_instances[server]['ram'] = 0
                    type4_instances[server]['hot_weight'] = 0
                    type4_instances[server]['cold_weight'] = 0
                    type4_instances[server]['cpu_util'] = 0
                    type4_instances[server]['latency'] = 0
                    type4_instances[server]['turnover'] = 0

                type4_instances = {}

                print 'spot instance terminated---'
                spot_fail_timer4 = 0

        """
        if spot_fail == True:
            spot_fail_timer += 1
            index = i_time / TP_INTERVAL
            print 'spot_fail_timer= %d' % spot_fail_timer
            if spot_fail_timer % spot_fail_interval == 1:
                print 'move data'
                m_delta_od = float(math.ceil(m_s[index] / (spot_fail_delay/spot_fail_interval)))
                m_delta_spot = -m_delta_od

                if spot_fail_timer == 1:
                    c_delta_od = c_s[index]
                # memory scale on-demand instance
                mem_scale(memcached_servers_od, G_M_MIN, G_M_MAX, G_C_MIN, False, True)
                # memory scale spot instance
                mem_scale(memcached_servers_spot, M_DEFAULT, M_DEFAULT, C_DEFAULT, True, True)
                if spot_fail_timer == 1:
                    # cpu scale on-demand instance
                    cpu_scale(memcached_servers_od, G_C_MIN, G_C_MAX, G_M_MIN, False, True)
                    # cpu scale spot instance
                    cpu_scale(memcached_servers_spot, C_DEFAULT, C_DEFAULT, M_DEFAULT, True, True)
                # weight scale
                x += (1-x_t[index])/(spot_fail_delay/spot_fail_interval)
                y += (1-y_t[index])/(spot_fail_delay/spot_fail_interval)
                weight_scale(memcached_servers_od, memcached_servers_spot, x, y)
                update_server(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
        
        

        if spot_fail_timer >= spot_fail_delay:
            index = i_time / TP_INTERVAL
            spot_fail_timer = 0
            spot_fail = False
            for server in memcached_servers_spot:
                memcached_servers_spot[server]['core'] = 0
                memcached_servers_spot[server]['ram'] = 0
                memcached_servers_spot[server]['hot_weight'] = 0
                memcached_servers_spot[server]['cold_weight'] = 0
                memcached_servers_spot[server]['cpu_util'] = 0
                memcached_servers_spot[server]['latency'] = 0
                memcached_servers_spot[server]['turnover'] = 0
            x_t[index] = 1
            y_t[index] = 1    
            print 'spot instance terminated---'
            """
        

        if i_time % T_STATUS == 0 and i_time > 0:

            get_status(memcached_servers_od, memcached_servers_spot, mcrouter_servers)
            tput_sum = sum(mcrouter_servers[server]['tput'] for server in mcrouter_servers)
            print "tput sum: %f" % tput_sum
            latency_ycsb = sum(mcrouter_servers[server]['latency'] for server in mcrouter_servers)/max(1,len(mcrouter_servers))
            print "average ycsb latency: %f" % latency_ycsb

            active_od = get_active_servers(memcached_servers_od)
            active_spot = get_active_servers(memcached_servers_spot)
            avg_latency = sum(active_od[server]['latency'] for server in active_od) + sum(active_spot[server]['latency'] for server in active_spot)
            if (len(active_spot) + len(active_od)) == 0:
                avg_latency = 0
            else:
                avg_latency = avg_latency / (len(active_spot) + len(active_od))
            print "average memcached latency: %f" % avg_latency

            print "active od: %d" % len(active_od)
            print "active spot: %d" % len(active_spot)

            m_o_t = sum(active_od[server]['ram'] for server in active_od)
            m_s_t = sum(active_spot[server]['ram'] for server in active_spot)
            c_o_t = sum(active_od[server]['core'] for server in active_od)
            c_s_t = sum(active_spot[server]['core'] for server in active_spot)

            print "m_o: %d" % m_o_t
            print "m_s: %d" % m_s_t
            print "c_o: %d" % c_o_t
            print "c_s: %d" % c_s_t

            print type1_instances
            print type2_instances
            print type3_instances
            print type4_instances
            print memcached_servers_od

            f_output = open('./results/output.txt','a+')
            output = '%d\t%f\t%f\t%f\t%d\t%d\t%d\t%d\t%d\t%d\n' % (i_time, tput_sum, latency_ycsb, avg_latency, len(active_od), len(active_spot), m_o_t, m_s_t, c_o_t, c_s_t)
            f_output.write(output)
            f_output.close()

            #write_server_stats_to_file(i_time,memcached_servers_od, 'od')
            #write_server_stats_to_file(i_time,memcached_servers_spot, 'spot')

        """#if i == 8*360+60: #add noise arrival
        if i_time == 9*TP_INTERVAL+300000:
            extra_noise = True
            index = i_time / TP_INTERVAL
            update_server_noise(memcached_servers_od, memcached_servers_spot, mcrouter_servers_noise)
            #index = 8
            # kill exist ycsb
            cmd = 'killall java'

            for server in mcrouter_servers_noise:
                run_cmd(server, cmd)
            time.sleep(1)

            cmd = '/home/ubuntu/ycsb/YCSB-master/bin/ycsb run memcached -P ycsb/YCSB-master/workloads/workloadc\
            -p recordcount=%d -p maxexecutiontime=3600 -p hot_keys_file=/home/ubuntu/hot_keys_folder/hot_keys_2_%d\
            -p random_seed=%d -p memcached.server=localhost:11211 -p enable_key_count_hashmap=false\
            -p enable_key_popularity_stat=false -p enable_key_partition=false -threads 30\
            -target %d -s > ycsb/YCSB-master/stats 2>&1'\
            % (working_set[index], index + 1, random_seed[index], math.ceil(2*arrival[index]/len(mcrouter_servers_noise)))

            for server in mcrouter_servers_noise:
	            run_cmd(server, cmd)

        if i_time == 16*TP_INTERVAL+300000:
            extra_noise = True
            index = i_time / TP_INTERVAL
            update_server_noise(memcached_servers_od, memcached_servers_spot, mcrouter_servers_noise)
            #index = 8
            # kill exist ycsb
            cmd = 'killall java'

            for server in mcrouter_servers_noise:
                run_cmd(server, cmd)
            time.sleep(1)

            cmd = '/home/ubuntu/ycsb/YCSB-master/bin/ycsb run memcached -P ycsb/YCSB-master/workloads/workloadc\
            -p recordcount=%d -p maxexecutiontime=3600 -p hot_keys_file=/home/ubuntu/hot_keys_folder/hot_keys_2_%d\
            -p random_seed=%d -p memcached.server=localhost:11211 -p enable_key_count_hashmap=false\
            -p enable_key_popularity_stat=false -p enable_key_partition=false -threads 30\
            -target %d -s > ycsb/YCSB-master/stats 2>&1'\
            % (working_set[index], index + 1, random_seed[index], math.ceil(1.5*arrival[index]/len(mcrouter_servers_noise)))

            for server in mcrouter_servers_noise:
	            run_cmd(server, cmd)

        if extra_noise == True:
            noise_timer += 1
            if noise_timer > noise_duration:
                #stop noise
                # kill exist ycsb
                cmd = 'killall java'

                for server in mcrouter_servers_noise:
                    run_cmd(server, cmd)
                time.sleep(1)

                extra_noise = False
                noise_timer = 0
        """

        print "Time: %d" % i_time
        i_time += 1
        time.sleep(1)
        T_DELTA += 1



if __name__ == '__main__':
    main()

