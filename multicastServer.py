#!/usr/bin/python

import socket
import struct
import sys
import time
import protocol
import select

from collections import defaultdict
from packet import *
from sender import *

number_of_clients = 2
sockets = []
receivers = ["pc3-014-l.cs.st-andrews.ac.uk", "pc3-009-l.cs.st-andrews.ac.uk"]
file_name = sys.argv[1]

# Set up an UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(protocol.socket_timeout)
ttl = struct.pack('b', protocol.time_to_live)
udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

# Make file's start of stream packet
startPacket = generate_start_packet(file_name)


# # Establishing connections with the receivers
for receiver in receivers:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((receiver, protocol.tcp_port))
    sock.setblocking(0)

    sockets.append(sock)
    print >> sys.stderr, "Connected to receiver: %s" % receiver
    sock.send(startPacket.pack())

clients_listening = 0
file_sent = False
ack_receivers = []

def all_clients_received():
	if len(ack_receivers) == number_of_clients:
		return True

	return False	


while True:
	input_ready, output_ready, _ = select.select(sockets, [], [])

	for socket in input_ready:
		data = socket.recv(protocol.max_packet_size)

		print >> sys.stderr, "Received: %d bytes" % len(data)

		if (data[:3] == protocol.name):
			if data[4:5] == protocol.success_packet_type:
				print >> sys.stderr, "Ack."

				print >> sys.stderr, ack_receivers

				if (file_sent == True):
					if (socket not in ack_receivers):
						ack_receivers.append(socket.getpeername())

				if all_clients_received() == True:
					print >> sys.stderr, "File succesfuly sent."
					for socket in sockets:
						socket.close()
					print >> sys.stderr, ack_receivers
					sys.exit(0)

				clients_listening += 1;

				if (number_of_clients == clients_listening and file_sent == False):
					send_data(udp_socket)

					print >> sys.stderr, "Sending the whole file..."

					file_sent = True

					for socket in sockets:
						print >> sys.stderr, len(StreamEndPacket.pack())
						socket.send(StreamEndPacket.pack())


			elif data[4:5] == protocol.request_packet_type:
					resend_data(data, udp_socket)

					for socket in sockets:
						socket.send(StreamEndPacket.pack())
					