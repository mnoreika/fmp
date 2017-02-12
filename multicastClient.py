#!/usr/bin/python

import socket
import struct
import sys
import protocol

from packet import *


# Creata a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
sock.bind(protocol.server_address)

group = socket.inet_aton(protocol.multicast_ip)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

packet_number = 0
packets_missed = []

def acknowledgeReceipt():
	sock.sendto('OK', address)
	print >> sys.stderr, 'Acknowledge response sent.'

	print >> sys.stderr, '\n# File is being transmitted #\n'


def parsePacket(data):
	global packet_number
	global packets_missed

	if (data[4:5] == protocol.start_packet_type):
		print >> sys.stderr, '\n# Start of transmission packet received #'

		packet_number = 0

		packets_missed = []

		readStreamStartPacket(data)

	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:10]);

		packet_number += 1

		if (packet[3] in packets_missed):
			packets_missed.remove(packet[3])

		elif (packet_number != packet[3]):
			packets_missed.append(packet_number)

			packet_number += 1


		readDataPacket(packet, data)

	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data)


def readStreamStartPacket(data):
	
	packet = StreamStartPacket.unpack(data)

	print >> sys.stderr, packet

	file_name = packet[5].split(b'\0',1)[0]
	print >> sys.stderr, 'File name: %s' % file_name

	global file

	file = open(file_name + ".received", "w+b")

	acknowledgeReceipt()


def readStreamEndPacket(data):
	packet = StreamEndPacket.unpack(data)

	print >> sys.stderr, "# End of stream packet received #"
	print >> sys.stderr, packet

	global packet_number
	print >> sys.stderr, "Packets received: %d\n" % (packet_number - len(packets_missed))

	if (len(packets_missed) != 0):
		# Check if packets are missing and request the mising ones 
		print >> sys.stderr, "Packets missed: %d \n %s" % (len(packets_missed), packets_missed)

		requestPacket = RequestPacket.packHeader(len(packets_missed)) + RequestPacket.packPayload(len(packets_missed) , packets_missed)

		print >> sys.stderr, "Sending request packet: %d bytes" % len(requestPacket)

	 	sock.sendto(requestPacket, address)
	else:
		success_packet = SuccessPacket.pack()

		print >> sys.stderr, "Sending success packet: %d bytes" % len (success_packet)

		sock.sendto(success_packet, address)
 
def readDataPacket(packet, data):
	file.seek(118 * (packet[3] - 1))

	file.write(data[10:(10 + packet[4])])

print >> sys.stderr, 'Waiting for data...'

# Receive the data and respond to the sender
while True:
	data, address = sock.recvfrom(1024)

	# print >> sys.stderr, 'Received %s bytes from %s' % (len(data), address)

	if (data[:3] == protocol.name):
		parsePacket(data)
	else:
		print >> sys.stderr, 'Invalid protocol. Packet dropped.'


