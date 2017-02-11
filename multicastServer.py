#!/usr/bin/python

import socket
import struct
import sys
import time
import protocol

from packet import *


# Sends the packet using multicast to multiple recipients
def sendPacket(packet):
	send = sock.sendto(packet, protocol.multicast_group)

	
# Create a datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout for the socket
sock.settimeout(protocol.socket_timeout)

# Set the time-to-live for messages
ttl = struct.pack('b', protocol.time_to_live)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

start_time = time.clock()

startPacket = StreamStartPacket("movie.mjpeg", 1024, 4171)

print >> sys.stderr, 'Start of stream packet sent.'

sendPacket(startPacket.pack())


# Look for responses from all recipients
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

				packet_number = 0

				while byte != "":
					payload.append(byte)

					if len(payload) == 118:
						
						packet_number += 1

						dataPacketHeader = DataPacket.packHeader(packet_number, 118)

						dataPacket = dataPacketHeader + payload;

						# print >> sys.stderr, 'Packet of length: %d was sent.' % len(dataPacket)
						sendPacket(dataPacket)
						payload = bytearray()	
					
					byte = f.read(1)

				packet_number += 1

				dataPacketHeader = DataPacket.packHeader(packet_number, len(payload))

				dataPacket = dataPacketHeader + payload;

				sendPacket(dataPacket)

				print >> sys.stderr, "Packets sent %d" % packet_number

		break

#Sending end of stream packet		
endPacket = StreamEndPacket.pack()

sendPacket(endPacket);

print >> sys.stderr, 'Waiting for confirmation of succesful file receipt...'

while True:
	try:
		data, server = sock.recvfrom(1024);
	except socket.timeout:
		print >> sys.stderr, 'Socket timed out.'
		break
	else:
		print >> sys.stderr, 'Received "%d" bytes from %s' % (len(data), server)

		if (data[:3] == protocol.name):
			if (data[4:5] == protocol.request_packet_type):
				print >> sys.stderr, "Request packet received."

				packet_header = RequestPacket.unpackHeader(data[:8])
				packet_payload = RequestPacket.unpackPayload(packet_header[3], data[8:])

				print >> sys.stderr, packet_header
				print >> sys.stderr, packet_payload
		else:
			print >> sys.stderr, "Invalid protocol. Packet dropped."		


end_time = time.clock()
		
print >> sys.stderr, "Time taken: %0.5f seconds" % (end_time - start_time)





