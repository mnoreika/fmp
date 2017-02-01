#!/usr/bin/python

import socket
import struct
import sys

multicast_group = '228.5.6.7'
server_address = ('', 6665)

# Creata a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
sock.bind(server_address)

group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Receive the data and respond to the sender
while True:
	print >> sys.stderr, 'Waiting for message...'
	data, address = sock.recvfrom(1024)

	print >> sys.stderr, 'Received %s bytes from %s' % len(data), address)
	# print >> sys.stderr, data

	print >> sys.stderr, 'Sending acknowledgement to the sender ', address
	sock.sendto('ack', address)