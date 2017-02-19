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

number_of_clients = 3
receivers = ["pc3-014-l.cs.st-andrews.ac.uk", "pc3-009-l.cs.st-andrews.ac.uk", "pc3-022-l.cs.st-andrews.ac.uk"]
file_name = sys.argv[1]

clients_ready = 0

current_window = 0
last_window = 0
last_window_size = 0

all_ready = False

ack_receivers = []

# Reads acknoledgement
def read_success_packet(socket, data):
	global ack_receivers
	global current_window
	global last_window
	global number_of_clients
	global last_window_size
	global all_ready

	packet = SuccessPacket.unpack(data[:8])

	# Indicate which receiver acknoledged success of receipt 
	if (socket.getpeername() not in ack_receivers and packet[3] == current_window):
		ack_receivers.append(socket.getpeername())


	# Determine if all receivers received the file
	if all_received(ack_receivers, number_of_clients) and current_window == last_window:
		print >> sys.stderr, "File succesfuly sent."
		
		sys.exit(0)


	if (all_ready == False and all_received(ack_receivers, number_of_clients)):
		send_data(udp_socket, file_name, current_window, protocol.window_size)

		for socket in sockets:
			socket.sendall(StreamEndPacket.pack(current_window), 2048)
			
		ack_receivers = []
		all_ready = True


	# When clients are ready, send the file
	if (all_ready == True and all_received(ack_receivers, number_of_clients)):

		# Moving to the next window
		current_window += 1

		ack_receivers = []

		if (current_window == last_window):
			send_data(udp_socket, file_name, current_window, last_window_size)
		else:
			send_data(udp_socket, file_name, current_window, protocol.window_size)	

		for socket in sockets:
			socket.sendall(StreamEndPacket.pack(current_window), 2048)


# Reads negative acknoledgement
def read_request_packet(data, file_name):
	global current_window

	resend_data(data, udp_socket, file_name, current_window)

	for socket in sockets:
		socket.sendall(StreamEndPacket.pack(current_window), 2048)

# Set up an UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(protocol.socket_timeout)
ttl = struct.pack('b', protocol.time_to_live)
udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

# Make file's start of stream packet
startPacket = generate_start_packet(file_name)

last_window = startPacket.number_of_windows
last_window_size = startPacket.last_window_size

file_name = startPacket.file_name

# Connect to receivers
sockets = connect_to_receivers(receivers, startPacket)


while True:
	input_ready, output_ready, _ = select.select(sockets, [], [], 0.1)

	# Read data from all sockets that are input ready
	for socket in input_ready:
			data = socket.recv(protocol.max_packet_size)
	
			if (data[:3] == protocol.name and data[3:4] == protocol.version):
				if data[4:5] == protocol.success_packet_type:
					read_success_packet(socket, data)

				elif data[4:5] == protocol.request_packet_type:
					read_request_packet(data, file_name)

	if not (input_ready or output_ready):
		for socket in sockets:
			socket.sendall(StreamEndPacket.pack(current_window), 2048)

	