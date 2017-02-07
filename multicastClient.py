#!/usr/bin/python

import socket
import struct
import sys
from packet import *

multicast_group = '228.5.6.7'
server_address = ('', 8886)



# Creata a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
sock.bind(server_address)

group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def acknowledgeReceipt():
	sock.sendto('OK', address)
	print >> sys.stderr, 'Acknowledge response sent.'


def readPacket(packet):
	if (packet[2] == start_packet_type):	
		print >> sys.stderr, 'Start packet read.'

		file_name = packet[5].split(b'\0',1)[0]
		print >> sys.stderr, 'File name: %s' % file_name

		global file

		file = open(file_name + ".received", "wb")

		global packets_received

		packets_received = 0

		acknowledgeReceipt()

	elif (packet[3] == end_packet_type):
		print >> sys.stderr, 'End packet read.'
	elif (packet[3] == data_packet_type):
		print >> sys.stderr, 'Data packet read.'


# Receive the data and respond to the sender
while True:
	print >> sys.stderr, 'Waiting for data...'
	data, address = sock.recvfrom(1024)

	print >> sys.stderr, 'Received %s bytes from %s' % (len(data), address)

	if (data[:3] == protocol_name):

		if (data[4:5] == start_packet_type):
			print >> sys.stderr, 'Start of transmission packet received.'
			packet = StreamStartPacket.unpack(data)

			print >> sys.stderr, packet

			print >> sys.stderr, 'Protocol: %s Version: %s' % (packet[0], packet[1])

			readPacket(packet)

		if (data[4:5] == data_packet_type):
			print >> sys.stderr, 'Data packet received.'

			packet = DataPacket.unpackHeader(data[:10]);

			print >> sys.stderr, packet

			print >> sys.stderr, "Length of packet: %d" % len(data[10:])

			print >> sys.stderr, 'Protocol: %s Version: %s' % (packet[0], packet[1])

			packets_received += 1

			file.write(data[10:(10 + packet[4])])

			print >> sys.stderr, data[10:(10 + packet[4])]

			print >> sys.stderr, "Packets received: %d" % packets_received

		if (data[4:5] == end_packet_type):

			packet = StreamEndPacket.unpack(data)

			print >> sys.stderr, "End of stream packet received"
			print >> sys.stderr, packet

			file.close()

	else:
		print >> sys.stderr, 'Invalid protocol. Packet dropped.'
