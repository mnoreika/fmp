import sys
import time
import os
import protocol
import socket
import time

from packet import *

# Global variables
global total_packets_sent
global window_checksum

total_packets_sent = 0
window_checksum = ''


# Sends end of stream message
def send_eos(sockets, current_window):
	global window_checksum

	for socket in sockets:
		socket.sendall(StreamEndPacket.pack(current_window, window_checksum), 2048)

# Makes a start of stream packet that contains the meta-data of the file being sent
def generate_start_packet(file_name):
	file_size = os.path.getsize(file_name)

	# Calculate the number of packets required to send the whole file
	if (file_size % protocol.data_payload_size == 0):
		number_of_data_packets =  file_size / protocol.data_payload_size 
	else:
		number_of_data_packets =  file_size / protocol.data_payload_size + 1

	# Calculate the number of windows of transmission required to send the packets	
	if (number_of_data_packets % protocol.window_size == 0):
		number_of_windows =  number_of_data_packets / protocol.window_size
		last_window_size = protocol.window_size 
	else:
		number_of_windows =  number_of_data_packets / protocol.window_size + 1
		last_window_size = number_of_data_packets - ((number_of_windows - 1) 
			* protocol.window_size)	

	# Calculate CRC32 signature of the file
	file_checksum = calculate_checksum(file_name)

	return StreamStartPacket(
		file_name, 
		protocol.data_payload_size, 
		number_of_data_packets, 
		number_of_windows - 1,
		last_window_size,
		file_checksum)

# Establishes TCP connections with the receivers
def connect_to_receivers(receivers, startPacket):
	sockets = []

	for receiver in receivers:
	    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    sock.connect((receiver, protocol.tcp_port))
	    sock.setblocking(0)
	    sockets.append(sock)

	    print >> sys.stderr, "Connected to receiver: %s" % receiver

		# Send start of stream packet, 2048 - MSG_CONFIRM flag
	    sock.sendall(startPacket.pack(), 2048)
	  
	return sockets	

# Sends the packet using multicast to multiple recipients
def send_udp(packet, udp_socket):
	send = udp_socket.sendto(packet, protocol.multicast_group)

# Reads the packet from file and sends it, returns data sent
def send_packet(packet, current_window, file, udp_socket):
	# Reading data for the required packet from file
	file.seek(current_window * protocol.window_size * 
		protocol.data_payload_size + (packet - 1) * protocol.data_payload_size)
	
	# Constructing the packet		
	dataPayload = file.read(protocol.data_payload_size)
	dataPacketHeader = DataPacket.packHeader(packet, current_window, len(dataPayload))
	dataPacket = dataPacketHeader + dataPayload	

	send_udp(dataPacket, udp_socket)

	return dataPayload

# Reads and sends one window of packets
def send_data(udp_socket, file_name, current_window, window_size):
	global total_packets_sent
	global window_checksum

	window_checksum = 0

	# Read window from file
	with open(file_name, "rb") as file:
		for packet in range(1, window_size + 1):
			data_sent = send_packet(packet, current_window, file, udp_socket)
			total_packets_sent += 1

			# Update the window CRC32 checksum with the current packet's data
			window_checksum = zlib.crc32(data_sent, window_checksum)

			# Sleep between each packet, if enabled
			time.sleep(protocol.transmission_delay)

	print >> sys.stderr, "Window %d sent" % current_window		
	print >> sys.stderr, "Packets sent: %d" % total_packets_sent	

	# Calculating the CRC32 checksum for the current window
	window_checksum = "%X"%(window_checksum & 0xFFFFFFFF)
	
# Reads packets that were missed by the receiver and sends them again
def resend_data(data, udp_socket, file_name, current_window, window_size):
	global packet_number

	# Trying to parse the request packet
	# Sometimes the packet has different size than expected and is dropped
	try:
		request_packet_header = RequestPacket.unpackHeader(data[:8])

		# Check if the whole window needs to be retransmitted, 0 indicates that
		if (request_packet_header[3] == 0):
			send_data(udp_socket, file_name, current_window, window_size)
			return	

		request_packet_payload = RequestPacket.unpackPayload(
			request_packet_header[3], data[8:8+(request_packet_header[3] * 2)])
	except:
		return

	

	# Iterate through the list of missing packets and resend them
	with open(file_name, "rb") as file:
		for missed_packet in request_packet_payload:
			send_packet(missed_packet, current_window, file, udp_socket)

			# Sleep before each packet, if enabled
			time.sleep(protocol.transmission_delay)


# Checks if all received got the file
def all_ack_received(ack_receivers, number_of_clients):
	if len(ack_receivers) == number_of_clients:
		return True

	return False	

