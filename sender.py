import sys
import time
import os
import protocol
import socket
import time

from packet import *

# Makes a start of stream packet that contains the meta-data of the file being sent
def generate_start_packet(file_name):

	file_size = os.path.getsize(file_name)

	if (file_size % protocol.data_payload_size == 0):
		number_of_data_packets =  file_size / protocol.data_payload_size 
	else:
		number_of_data_packets =  file_size / protocol.data_payload_size + 1	

	return StreamStartPacket(file_name, protocol.data_payload_size, number_of_data_packets)

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
	    sock.send(startPacket.pack())

	  
	return sockets	

# Sends the packet using multicast to multiple recipients
def sendPacket(packet, udp_socket):
	send = udp_socket.sendto(packet, protocol.multicast_group)

def send_data(udp_socket, file_name, current_window):
	with open(file_name, "rb") as file:
		for packet in range(1, protocol.window_size + 1):
			file.seek(current_window * protocol.window_size * protocol.data_payload_size + (packet - 1) * protocol.data_payload_size)
			dataPayload = file.read(protocol.data_payload_size)
			dataPacketHeader = DataPacket.packHeader(packet, len(dataPayload))
			dataPacket = dataPacketHeader + dataPayload	
			sendPacket(dataPacket, udp_socket)

			time.sleep(protocol.transmission_delay)

	print >> sys.stderr, "Window %d sent" % current_window		
	

def resend_data(data, udp_socket):
	global packet_number

	print >> sys.stderr, len(data)

	print >> sys.stderr, RequestPacket.unpackHeader(data[:8])

	request_packet_header = RequestPacket.unpackHeader(data[:8])

	request_packet_payload = RequestPacket.unpackPayload(request_packet_header[3], data[8:8 + (request_packet_header[3] * 2)])

	with open("movie.mjpeg", "rb") as file:
		for missed_packet in request_packet_payload:
			file.seek((missed_packet - 1) * 118)
			dataPayload = file.read(118)
			dataPacketHeader = DataPacket.packHeader(missed_packet, len(dataPayload))
			dataPacket = dataPacketHeader + dataPayload	
			sendPacket(dataPacket, udp_socket)


# Checks if all received got the file
def all_received(ack_receivers, number_of_clients):
	if len(ack_receivers) == number_of_clients:
		return True

	return False	

