#!/usr/bin/python

import socket
import struct
import sys
import protocol
import select

from packet import *
from packet_parser import *

# Set up udp socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(protocol.server_address)
group = socket.inet_aton(protocol.multicast_ip)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Set up tcp socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_socket.bind(("", protocol.tcp_port))
tcp_socket.listen(5)


sockets = [udp_socket]

print >> sys.stderr, 'Waiting for data...\n'

# Receive the data and respond to the sender
while True:
	# Connect to a receiver if currently not receiving
	if len(sockets) == 1:
		tcp_conn, client_address = tcp_socket.accept()
		sockets.append(tcp_conn)
		print >> sys.stderr, "Connection with sender established:", client_address


	input_ready, output_ready, _ = select.select(sockets, [], [])

	for socket in input_ready:
		try:
			data, address = socket.recvfrom(protocol.max_packet_size)
		except:
			print >> sys.stderr, "Connection closed by the sender.\n"
		
		if data:
			if (data[:3] == protocol.name and data[3:4] == protocol.version):
				parsePacket(data, tcp_conn)
			else:
				print >> sys.stderr, 'Invalid protocol. Packet dropped.'
		else:
			socket.close()
			sockets.remove(tcp_conn)

          
			
