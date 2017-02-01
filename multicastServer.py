#!/usr/bin/python

import socket
import struct
import sys

message = 'binary data'
multicast_group = ('228.5.6.7', 6665)

# Reads the file and plits into smaller chunks
def splitFile(input_file, chunck_size):
	# Read the file
	file = open(input_file, 'rb')
	data = file.read()
	file.close()

	bytes = len(data)

	chunks = []
	for i in range(0, bytes + 1, chunck_size):
		chunks.append(data[i : i + chunck_size])


	return chunks	

# Create a datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout for the socket
sock.settimeout(0.2)

# Set the time-to-live for messages
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

# Send message to multiple clients
try:
	dataChunks = splitFile("movie.mjpeg", 1024)

	# Send data to multicast group
	for i in range(0, len(dataChunks)):
		send = sock.sendto(dataChunks[i], multicast_group)
		print >> sys.stderr, 'Chunk sent.'

	# Look for responses from all recipients
	while True:
		print >> sys.stderr, 'Waiting for confirmation of success...'

		try:
			data, server = sock.recvfrom(16);
		except socket.timeout:
			print >> sys.stderr, 'Socket timed out.'
			break
		else:
			print >> sys.stderr, 'Received "%s" from %s' % (data, server)	

finally:
	sock.close()
	print >> sys.stderr, 'Socket connection closed.'




