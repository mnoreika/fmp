#!/usr/bin/python

import socket
import struct
import sys
from packet import *

multicast_group = '228.5.6.7'
server_address = ('', 6665)

# Creata a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
sock.bind(server_address)

group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

global file

def acknowledgeReceipt():
	sock.sendto('OK', address)
	print >> sys.stderr, 'Acknowledge response sent.'


def readPacket(packet):
	if (packet[2] == start_packet_type):	
		print >> sys.stderr, 'Start packet read.'

		file_name = packet[5].split(b'\0',1)[0]
		print >> sys.stderr, 'File name: %s' % file_name

		file = open (file_name, "wb")

		acknowledgeReceipt()

	elif (packet[3] == end_packet_type):
		print >> sys.stderr, 'End packet read.'
	elif (packet[3] == data_packet_type):	
		print >> sys.stderr, 'Data packet read.'


# Receive the data and respond to the sender
while True:
	print >> sys.stderr, 'Waiting for data...'
	data, address = sock.recv(1024)

	print >> sys.stderr, 'Received %s bytes from %s' % (len(data), address)

	if (len(data) == 44):
		packet = StreamStartPacket.unpack(data)

	if (len(data) == 44 and packet[0]  == protocol_name and packet[1] == protocol_version):
		print >> sys.stderr, 'Protocol: %s Version: %d' % (protocol_name, protocol_version)
		print >> sys.stderr, StreamStartPacket.unpack(data)

		readPacket(packet)
	else:
		print >> sys.stderr, 'Invalid protocol. Packet dropped.'

	# print >> sys.stderr, data

	# print >> sys.stderr, 'Sending acknowledgement to the sender ', address
	# sock.sendto('OK', address)	