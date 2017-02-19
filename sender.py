import sys
import time
import os
import protocol
import socket
import time

from packet import *

global total_sent
total_sent = 0

# Makes a start of stream packet that contains the meta-data of the file being sent
def generate_start_packet(file_name):
	file_size = os.path.getsize(file_name)

	if (file_size % protocol.data_payload_size == 0):
		number_of_data_packets =  file_size / protocol.data_payload_size 
	else:
		number_of_data_packets =  file_size / protocol.data_payload_size + 1

	if (number_of_data_packets % protocol.window_size == 0):
		number_of_windows =  number_of_data_packets / protocol.window_size
		last_window_size = protocol.window_size 
	else:
		number_of_windows =  number_of_data_packets / protocol.window_size + 1
		last_window_size = number_of_data_packets - ((number_of_windows - 1) * protocol.window_size)	

		print >> sys.stderr, last_window_size

	return StreamStartPacket(
		file_name, 
		protocol.data_payload_size, 
		number_of_data_packets, 
		number_of_windows - 1,
		last_window_size)

# Establishes TCP connections with the receivers
def connect_to_receivers(receivers, startPacket):
	sockets = []

	for receiver in receivers:
	    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    sock.connect((receiver, protocol.tcp_port))
	    sock.setblocking(0)
	    sockets.append(sock)

	    print >> sys.stderr, "Connected to receiver: %s" % receiver

		# Send start of stream packet
	    sock.sendall(startPacket.pack(), 2048)

	  
	return sockets	

# Sends the packet using multicast to multiple recipients
def sendPacket(packet, udp_socket):
	send = udp_socket.sendto(packet, protocol.multicast_group)

def send_data(udp_socket, file_name, current_window, window_size):
	global total_sent

	with open(file_name, "rb") as file:
		for packet in range(1, window_size + 1):
			file.seek(current_window * protocol.window_size * protocol.data_payload_size + (packet - 1) * protocol.data_payload_size)
			dataPayload = file.read(protocol.data_payload_size)
			dataPacketHeader = DataPacket.packHeader(packet, current_window, len(dataPayload))
			dataPacket = dataPacketHeader + dataPayload	
			sendPacket(dataPacket, udp_socket)

			total_sent += 1
				
			time.sleep(protocol.transmission_delay)

	print >> sys.stderr, "Window %d sent" % current_window		
	print >> sys.stderr, "Packets sent: %d" % total_sent	
	

def resend_data(data, udp_socket, file_name, current_window):
	global packet_number

	request_packet_header = RequestPacket.unpackHeader(data[:8])

	request_packet_payload = RequestPacket.unpackPayload(request_packet_header[3], data[8:8 + (request_packet_header[3] * 2)])

	with open(file_name, "rb") as file:
		for missed_packet in request_packet_payload:
			file.seek(current_window * protocol.window_size * protocol.data_payload_size + (missed_packet - 1) * protocol.data_payload_size)
			dataPayload = file.read(protocol.data_payload_size)
			dataPacketHeader = DataPacket.packHeader(missed_packet, current_window, len(dataPayload))
			dataPacket = dataPacketHeader + dataPayload	
			sendPacket(dataPacket, udp_socket)

			time.sleep(protocol.transmission_delay)


# Checks if all received got the file
def all_received(ack_receivers, number_of_clients):
	if len(ack_receivers) == number_of_clients:
		return True

	return False	

