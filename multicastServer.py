#!/usr/bin/python

import socket
import struct
import sys
# from header import Header
from packet import DataPacket
from packet import StreamStartPacket
from packet import StreamEndPacket


# Sends the packet using multicast to multiple recipients
def sendPacket(packet):
	send = sock.sendto(packet, multicast_group)

def streamFile(file_name):
	try:

	    with open(file_name, "rb") as f:
				byte = f.read(1)
				payload = bytearray()

				while byte != "":
					payload.append(byte)

					if len(payload) == 128:

						print >> sys.stderr, 'Packet of length: %d was sent.' % len(payload)
						sendPacket(payload)
						payload = bytearray()
					
					byte = f.read(1)

				sendPacket(payload)	

	finally:
		sock.close()

	


multicast_group = ('228.5.6.7', 6665)

# Create a datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout for the socket
sock.settimeout(0.2)

# Set the time-to-live for messages
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


startPacket = StreamStartPacket("movie.jpmeg", 1024, 4171)

print >> sys.stderr, 'Start of stream packet sent.'

sendPacket(startPacket.pack())



# # Look for responses from all recipients
while True:
	print >> sys.stderr, 'Waiting for confirmation of receipt...'

	try:
		data, server = sock.recvfrom(16);
	except socket.timeout:
		print >> sys.stderr, 'Socket timed out.'
		break
	else:
		print >> sys.stderr, 'Received "%s" from %s' % (data, server)
		print >> sys.stderr, 'Starting file transmission...'

		with open("movie.mjpeg", "rb") as f:
				byte = f.read(1)
				payload = bytearray()

				while byte != "":
					payload.append(byte)

					if len(payload) == 128:

						print >> sys.stderr, 'Packet of length: %d was sent.' % len(payload)
						sendPacket(payload)
						payload = bytearray()
					
					byte = f.read(1)

				sendPacket(payload)	
		break
	

		






