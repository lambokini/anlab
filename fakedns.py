#!/usr/bin/python
"""													"""
"""                    Fakedns.py					"""
"""    A regular-expression based DNS MITM Server	"""
"""						by: Crypt0s					"""
# Adapted from https://github.com/jimmykane/Roque-Dns-Server to follow DNS specs-ish
# Jimmykane's version was in turn modified from an activestate recipe : http://code.activestate.com/recipes/491264-mini-fake-dns-server/
# I then modified it to be more efficient, support a config file, regular expression matching, passthrough requests, and proper "not found" responses

import socket
import re
import sys
import os
import threading
from socket import error
import select

exit_loop = False

class DNSQuery:
  def __init__(self, data):
    self.data=data
    self.dominio=''

    tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
    if tipo == 0:                     # Standard query
      ini=12
      lon=ord(data[ini])
      while lon != 0:
        self.dominio+=data[ini+1:ini+lon+1]+'.'
        ini+=lon+1
        lon=ord(data[ini])

class Respuesta:
    def __init__(self, query,re_list):
        self.data = query.data
        self.packet=''
        ip = None
        for rule in re_list:
            result = rule[0].match(query.dominio)
            if result is not None:
                ip = rule[1]
                print ">> Matched Request: " + query.dominio + ":" + ip
        # We didn't find a match, get the real ip
        if ip is None:
            try:
                ip = socket.gethostbyname(query.dominio)
                print ">> Unmatched request: " + query.dominio + ":" + ip
            except:
                # That domain doesn't appear to exist, build accordingly
                print ">> Unable to parse request:" + query.dominio
                # Build the response packet
                self.packet+=self.data[:2] + "\x81\x83"                         # Reply Code: No Such Name
                #							0 answer rrs   0 additional, 0 auth
                self.packet+=self.data[4:6] + '\x00\x00' + '\x00\x00\x00\x00'   # Questions and Answers Counts
                self.packet+=self.data[12:]                                     # Original Domain Name Question

        # Quick Hack
        if self.packet == '':
            # Build the response packet
            self.data[:2] #transaction ID
            self.packet+=self.data[:2] + "\x81\x80"
            self.packet+=self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
            self.packet+=self.data[12:]                                         # Original Domain Name Question
            self.packet+='\xc0\x0c'                                             # Pointer to domain name
            self.packet+='\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
            self.packet+=str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP

class ruleEngine:
    def __init__(self,file):
        self.re_list = []
        print '>>', 'Parse rules...'
        with open(file,'r') as rulefile:
            rules = rulefile.readlines()
            for rule in rules:
                splitrule = rule.split()

                # If the ip is 'self' transform it to local ip.
                if splitrule[1] == 'self':
                    ip = socket.gethostbyname(socket.gethostname())
                    splitrule[1] = ip

                self.re_list.append([re.compile(splitrule[0]),splitrule[1]])
                print '>>', splitrule[0], '->', splitrule[1]
            print '>>', str(len(rules)) + " rules parsed"


class dns_service (threading.Thread):
	def __init__(self, re_list):
		threading.Thread.__init__(self)
		self.re_list = re_list
		self.udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udps.setblocking(0)
		self.udps.bind(('',53))
		
		self.default_ip = '192.168.152.1'
		
		#print "xx"
	def run(self):
		global exit_loop
		timeout_in_seconds = 2
		while not exit_loop:
			try:
				ready = select.select([self.udps], [], [], timeout_in_seconds)
				if ready[0]:
					data, addr = self.udps.recvfrom(1024)
					p=DNSQuery(data)
					response = Respuesta(p,self.re_list).packet
					self.udps.sendto(response, addr)
			except error:
				break
	def quit(self):
		self.udps.close()
		
if __name__ == '__main__':
	global exit_loop
	# Default config file path.
	path = 'dns.conf'
	
	# Specify a config path.
	if len(sys.argv) == 2:
		path = sys.argv[1]
	
	if not os.path.isfile(path):
		print '>> Please create a "dns.conf" file or specify a config path: ./fakedns.py [configfile]'
		exit()	
	try:
		rules = ruleEngine(path)
		#print rules.re_list
		re_list = rules.re_list
	
		dns_server = dns_service(re_list)
		dns_server.start()	
		while True:
			dns_rule = raw_input("fakedns::rule>>")
			splitrule = dns_rule.split()
			if len(splitrule) < 2:
				if len(splitrule) == 0:
					continue
					
				if splitrule[0].lower() == 'quit':
					break
				elif splitrule[0].lower() == 'help' or splitrule[0].lower() == '?' :
					print "add new rule, use format google.* ip.\nfor examples *.example.com 192.168.0.100"
					
				continue
			# If the ip is 'self' transform it to local ip.
			if splitrule[1] == 'self':
					ip = socket.gethostbyname(socket.gethostname())
					splitrule[1] = ip
			
			rules.re_list.append([re.compile(splitrule[0]),splitrule[1]])
				
	except KeyboardInterrupt:
		print 'Receive singals to stop'
	
	print 'Quiting now ...'
	exit_loop = True
	dns_server.quit()
	dns_server.join()
		#
