#!/usr/bin/env python

import json
import re
import socket
import sys
import subprocess
from subprocess import PIPE
from subprocess import Popen
import telnetlib
import threading
import time
from urllib2 import urlopen

public_ip = ''


#If mcrouter-daemon is next to config file
def set_weights(data):
    configFile = 'mcrouter-install/install/mcrouter-config'
    fd = open(configFile,'w')
    fd.write(data)
    print 'set_weights complete'

def get_servers_stat():

    server = ''
    value = ''
    tmp = ''
    name = ['avg_latency_us']
    servers_dic = {}
    msg = ''
# read stats servers from telnet to port 5000
    global public_ip
    tn = telnetlib.Telnet(public_ip, 11211)
    tn.write('stats servers\n')
    data = tn.read_until('END')
    tn.write('quit\n')

    for line in data.splitlines():   #format:STAT 130.203.37.249:49161:TCP:ascii-1000 avg_latency_us:0.000 pending_reqs:0 inflight_reqs:0 new:8
		if name[0] in line:
			tmp = line.split(' ')[1]
			server = tmp.split(':')[0]+':'+tmp.split(':')[1]
			tmp = line.split(' ')[2]
			value = tmp.split(':')[1]
			if value is '':
				value = '0'
			servers_dic[server] = value
			#break
    msg = json.dumps(servers_dic)
    print msg
    print 'get:servers_stats done'
    return msg

def run_cmd(command):
	pid = subprocess.Popen(command, shell = True)
	#pid.communicate()
	print 'run:'+command+'done'

def reset_all():
	global public_ip
	#tn = telnetlib.Telnet('localhost', 11211)
	tn = telnetlib.Telnet(public_ip, 11211)
	tn.write('stats reset\n')
	tn.write('quit\n')
	print 'reset:all done'

def is_match(line):
	pattern = '.+ (.+) current ops/sec; .+'
	result = re.search(pattern, line)
	if result:
		return True
	else:
		return False

def is_match_lat(line):
        pattern = '.+\[READ AverageLatency\(us\)=(.+)\]'
        result = re.search(pattern, line)
        if result:
                return True
        else:
                return False


def main():
    # run mcrouter
	cmd = 'killall mcrouter'
	p = subprocess.Popen(cmd, shell=True)
	p.communicate()[0]
	cmd = 'mcrouter-install/install/bin/mcrouter -f mcrouter-install/install/mcrouter-config -p 11211 --num-proxies=8'

	ret = subprocess.Popen(cmd, shell=True)
	'''
	n_try = 0
	while ret.returncode is not 0 and n_try<5:
		time.sleep(2)
		n_try += 1
		ret = subprocess.Popen(cmd, shell=True)

	if n_try == 5 or (ret is not 0):
		print 'container failed'
		return
	'''
	#global cpu_util
	#cpu_util = 0
	global public_ip
	public_ip = urlopen('http://ip.42.pl/raw').read()
	#get_servers_stat()
	#private_ip = socket.gethostbyname(socket.gethostname())

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_address = ('', 12345) #this binds to any interface so you can use the public ip to connect to it
	print >>sys.stderr, 'starting up on %s port %s' % server_address
	sock.bind(server_address)

	sock.listen(1)


	try:
		while True:

			print >> sys.stderr, 'waiting for a connection'
			connection, client_address = sock.accept()

			try:
				print >>sys.stderr, 'connection from', client_address

				data = connection.recv(10240).rstrip()
				#print >>sys.stderr, 'received "%s"' % data
				if data:
					cmd = data.split('$')[0]
					obj = data.split('$')[1]

					if cmd == 'set':
							config = data.split('$')[2]
							if obj == 'weights':   #e.g., set:core:3
								print 'weights adjusment in progress...'
								set_weights(config)
							else:
									print >>sys.stderr, 'client sends unknown set:obj'
							connection.sendall('Set done.')
					elif cmd == 'run':
							run_cmd(obj)
							connection.sendall('Run command Done.')
					elif cmd == 'get':
							if obj == 'servers':   #get:servers    return average latency for all servers
									msg = get_servers_stat()
                                    					connection.sendall(msg)
                            				elif obj == 'tput':
                                    					with open('ycsb/YCSB-master/stats') as f:
                                            						lines = f.readlines()
											tputs = filter(is_match, lines)
                                                                                        tlat = filter(is_match_lat, lines)
									if tputs:
											match = re.search('.+ (.+) current ops/sec; .+', tputs[-1])
									else:
											match = None
                                                                        if tlat:
                                                                                        match_lat = re.search('.+\[READ AverageLatency\(us\)=(.+)\]',tlat[-1])
									else:
                   									match_lat = None

                                            				if match:
                                                    					#connection.sendall(match.group(1))
											msg = match.group(1)
									else:
											#connection.sendall('0')
											msg = '0'
                                                                        if match_lat:
                                                                                        msg = msg + ',' + match_lat.group(1)
                                                                        else:
                                             						msg = msg + ',0' 
									connection.sendall(msg)
							#elif obj == 'cpu_util':
							else:
									print >>sys.stderr, 'client sends unknown get:obj'
					elif cmd == 'reset':
							if obj == 'all': #reset:all    reset cmd_get, cmd_set, curr_item, etc
									reset_all()
									connection('Reset Done')
							else:
									print >>sys.stderr, 'client sends unknown reset:obj'
					else:
							print >>sys.stderr, 'client sends unknown cmd'
				else:
						print >>sys.stderr, 'client sends nothing'

			finally:
					connection.close()
					#sys.exit(-1)
	except KeyboardInterrupt:
			pass

if __name__ == "__main__":
        main()
                                                                                        

