#!/usr/bin/env python

import json
import socket
import sys
import subprocess
from subprocess import PIPE
import telnetlib
import threading
import time
from urllib2 import urlopen

public_ip = ''
cpu_util_vector = [0 for x in range(10)]

class ThreadMemcachedCpu (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
		global cpu_util_vector   #a string
		interval = 2   #seconds. obtain cpu util value every interval
		N = 10   # number of sample cpu util values stored at max
		cmd = "top -n 1 -b | grep memcached"
		index = 0
		try:
			while True:
				if index == N:
					index = 0
				p = subprocess.Popen(cmd, stdout=PIPE, shell=True)
				data = p.stdout.read().rstrip()
                                #print 'cpu util is %s' % data
				if not data:
					t_cpu_util = 0
				else:
					t_cpu_util = float(data.split()[8])
                                #print t_cpu_util
				cpu_util_vector[index] = t_cpu_util
				index += 1
				time.sleep(interval)
		except KeyboardInterrupt:
			pass


def connectToserver(ip, port):
	print 'connect to %s, %s'%(ip,str(port))
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (ip, int(port))
	sock.connect(server_address)
	if sock is None:
		print >>sys.stderr, 'cannot connect to server'
	return sock


def run_cmd(command):
	pid = subprocess.Popen(command,shell=True)
	#pid.communicate()
	print 'run:'+command+'done'


def set_core(core):
	c = int(core)
    quota = core-c
	if c == 1: #index of core starts from 0
		value = '0'
	else:
		value = '0-%d'%(c-1)
	#obtain container id; since there is only one container, we only need the first container id
	cmd = "sudo docker ps | sed -n 2p | cut -d ' ' -f 1"
	print cmd
	p = subprocess.Popen(cmd, stdout=PIPE, shell=True)
	container_id_short = p.stdout.read().rstrip()
	cmd = 'sudo docker ps -a --no-trunc -q | grep %s'%container_id_short
	print cmd
	p = subprocess.Popen(cmd, stdout=PIPE, shell=True)
	container_id = p.stdout.read().rstrip()
	#change the ACL of cpuset.cpus. It was -rw-r--r-- root root
	cmd1 = 'sudo chmod 666 /sys/fs/cgroup/cpuset/docker/%s/cpuset.cpus'%container_id
	print cmd1
	p1 = subprocess.Popen(cmd1,shell=True)
	p1.communicate()
	cmd2 = 'sudo echo %s > /sys/fs/cgroup/cpuset/docker/%s/cpuset.cpus'%(value,container_id)
	print cmd2
	p2 = subprocess.Popen(cmd2,shell=True)
	p2.communicate()
    
	print 'set:core done'


def set_ram(ram):  #ram is integer in MB
	try: #mem_limit
		port = '5001'
		global public_ip
		sock = connectToserver(public_ip, port)
		msg = 'mem_limit:%s'%ram
		sock.sendall(msg)
		data = sock.recv(1024)
		print >>sys.stderr, 'received thread_count feedback %s' %data
	finally:
		sock.close()
		#sys.exit(-1)
	print 'set:ram done'


def get_cpu_util():
	global cpu_util_vector
        #print cpu_util_vector
	avg_cpu_util = float(sum(cpu_util_vector))/max(len(cpu_util_vector),1)
	return avg_cpu_util

def get_stats_data():
	global public_ip
	tn = telnetlib.Telnet(public_ip, 11211)
	tn.write('stats\n')
	data = tn.read_until('END')
	tn.write('quit\n')
	return data


def get_single_stat(name, data):
	value = ''
	for line in data.splitlines():   #format:  STAT   name   value
		if name in line:
			value = line.split(' ')[2]
			break
	if value is '':
		value = '0'
	return value


def get_all():
	data = get_stats_data()
	names = ['curr_items', 'cmd_get', 'cmd_set', 'evictions', 'get_misses']
	temp_dict = {}
	for name in names:
		value = get_single_stat(name, data)
		temp_dict[name] = value

	#obtain cpu util of memcached process
	avg_cpu_util = get_cpu_util()  #float
	temp_dict['cpu_util'] = str(avg_cpu_util)

	msg = json.dumps(temp_dict)
	print msg
	print 'get:all done'
	return msg


def reset_all():
	global public_ip
	#tn = telnetlib.Telnet('localhost', 11211)
	tn = telnetlib.Telnet(public_ip, 11211)
	tn.write('stats reset\n')
	tn.write('quit\n')
	print 'reset:all done'


def flush_all():
	global public_ip
	#tn = telnetlib.Telnet('localhost', 11211)
	tn = telnetlib.Telnet(public_ip, 11211)
	tn.write('flush_all\n')
	tn.write('quit\n')
	print 'flush:all done'



def main():

    #kill any existing container
    cmd = "sudo docker ps | sed -n 2p | cut -d ' ' -f 1"
    print cmd
    p = subprocess.Popen(cmd, stdout=PIPE, shell=True)
    data = p.stdout.read()
    if data:
        container_id_short = data.rstrip()
        cmd = 'sudo docker stop %s' % container_id_short
        subprocess.Popen(cmd, shell=True)
        time.sleep(5)

	#start docker container which automatically starts memcached as a service
	cmd = "sudo docker run -d -p 11211:11211 -p 5001:5001 memcached_img"
	print cmd
	subprocess.Popen(cmd, shell=True)
	#p.communicate()
	print 'docker container started'

	global cpu_util
	cpu_util = 0
	try:
		ThreadMemcachedCpu().start()
	except (KeyboardInterrupt, SystemExit):
		cleanup_stop_thread();
		sys.exit()


	#global private_ip
	global public_ip
	public_ip = urlopen('http://ip.42.pl/raw').read()
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

				data = connection.recv(1024).rstrip()
				print >>sys.stderr, 'received "%s"' % data
				if data:
					cmd = data.split(':')[0]
					obj = data.split(':')[1]

					if cmd == 'set':
						value = int(data.split(':')[2])
						if obj == 'core':   #e.g., set:core:3
							set_core(value)
							msg = 'set core done'
						elif obj == 'ram':   #e.g., set:ram:8192  (MB)
							set_ram(value)
							msg = 'set ram done'
						else:
							print >>sys.stderr, 'client sends unknown set:obj'
						connection.sendall(msg)
					elif cmd == 'get':
						if obj == 'all': #get:all    Here all means all the stats needed by default
							msg = get_all()
							connection.sendall(msg)
						#elif obj == 'cpu_util':
						else:
							print >>sys.stderr, 'client sends unknown get:obj'
							connection.sendall('client sends unknown get:obj')
					elif cmd == 'reset':
						if obj == 'all': #reset:all    reset cmd_get, cmd_set, curr_item, etc
							reset_all()
							connection.sendall('reset all done')
						else:
							print >>sys.stderr, 'client sends unknown reset:obj'
							connection.sendall('client sends unknown reset:obj')
					elif cmd == 'flush': #flush:all
						flush_all()
						connection.sendall('flush all done')
					elif cmd == 'exit':  #exit:exit
						connection.sendall('begin to exit')
						return
					elif cmd == 'run':
						run_cmd(obj)
						connection.sendall('run cmd done')
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
