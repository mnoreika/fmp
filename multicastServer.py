#!/usr/bin/python

import socket
import struct
import sys
import time
import protocol
import select

from packet import *
from sender import *

# Sends a window of packets
def send_window():
	# Send number of packets according to the current window's size
	if (current_window == last_window):
		send_data(udp_socket, file_name, current_window, last_window_size)
	else:
		send_data(udp_socket, file_name, current_window, protocol.window_size)	

	send_eos(sockets, current_window)


# Reads acknowledgment
def read_success_packet(socket, data):
	global ack_receivers
	global current_window
	global number_of_clients
	global ready_to_transmit

	packet = SuccessPacket.unpack(data[:8])

	# Indicate which receiver acknowledged success of receipt 
	if (socket.getpeername() not in ack_receivers and packet[3] == current_window):
		ack_receivers.append(socket.getpeername())	

	# Determine if all receivers received the file
	if all_ack_received(ack_receivers, number_of_clients) and current_window == last_window:
		# Handle edge case, where the last window is the first winidow
		if (ready_to_transmit):
			print >> sys.stderr, "File successfully sent."
			sys.exit(0)

	# Wait for acknoledgement of start of stream packet receipt from all the clients
	if (ready_to_transmit == False and all_ack_received(ack_receivers, number_of_clients)):
		# Send the packets in the 0th window
		send_data(udp_socket, file_name, current_window, protocol.window_size)

		# Send end of stream
		send_eos(sockets, current_window)
			
		ack_receivers = []
		ready_to_transmit = True


	# When clients are ready, send the file
	if (ready_to_transmit == True and all_ack_received(ack_receivers, number_of_clients)):
		# Moving to the next window
		current_window += 1

		ack_receivers = []

		send_window()


# Reads negative acknowledgment
def read_request_packet(data, file_name):	
	# Resend packets of a particular window
	if (current_window == last_window):
			resend_data(data, udp_socket, file_name, current_window, last_window_size)
	else:
			resend_data(data, udp_socket, file_name, current_window, protocol.window_size)
	

	send_eos(sockets, current_window)

# Global variables
receivers = ["pc3-014-l.cs.st-andrews.ac.uk", "pc3-009-l.cs.st-andrews.ac.uk"]
number_of_clients = len(receivers)
file_name = sys.argv[1]
current_window = 0
last_window = 0
last_window_size = 0
ready_to_transmit = False
ack_receivers = []

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

# Listening for control messages from the receivers
while True:
	input_ready, output_ready, exception_ready = select.select(sockets, [], [], protocol.read_timeout)

	# Read data from all sockets that are input ready
	for socket in input_ready:
			data = socket.recv(protocol.tcp_buffer)
			
			# Determine if the received packet has the right protocol name and version
			if (data[:3] == protocol.name and data[3:4] == protocol.version):
				# Parse the packet depending on its type
				if data[4:5] == protocol.success_packet_type:
					read_success_packet(socket, data)

				elif data[4:5] == protocol.request_packet_type:
					read_request_packet(data, file_name)

	# In case of timeout, resend the end of stream packet
	if not (input_ready or output_ready):
		send_eos(sockets, current_window)

	