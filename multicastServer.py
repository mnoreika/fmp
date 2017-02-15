#!/usr/bin/python

import socket
import struct
import sys
import time
import protocol
import select

from packet import *

number_of_clients = 2
sockets = []
receivers = ["pc3-010-l.cs.st-andrews.ac.uk", "pc3-009-l.cs.st-andrews.ac.uk"]

start_time = time.clock()

# Sends the packet using multicast to multiple recipients
def sendPacket(packet):
	send = udp_sock.sendto(packet, protocol.multicast_group)

start_time = time.clock()

# Create a datagram socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout for the socket
udp_sock.settimeout(protocol.socket_timeout)

# Set the time-to-live for messages
ttl = struct.pack('b', protocol.time_to_live)
udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


startPacket = StreamStartPacket("movie.mjpeg", 1024, 4171)

# Establishing connections with the receivers
for receiver in receivers:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((receiver, protocol.tcp_port))
    sockets.append(sock)
    print >> sys.stderr, "Connected to receiver: %s" % receiver
    sock.send(startPacket.pack())

clients_listening = 0
file_sent = False

while True:
	input_ready, output_ready, _ = select.select(sockets, [], [])

	for socket in input_ready:
		data, address = socket.recvfrom(protocol.max_packet_size)

		print >> sys.stderr, "Received: %d bytes" % len(data)

		if data[4:5] == protocol.success_packet_type:

			clients_listening += 1;

			if (number_of_clients == clients_listening):
				with open("movie.mjpeg", "rb") as file:
					byte = file.read(1)
					payload = bytearray()

					packet_number = 0

					while byte != "":
						payload.append(byte)

						if len(payload) == 118:
							
							packet_number += 1

							dataPacketHeader = DataPacket.packHeader(packet_number, 118)

							dataPacket = dataPacketHeader + payload

							sendPacket(dataPacket)
							payload = bytearray()	
						
						byte = file.read(1)

					packet_number += 1

					dataPacketHeader = DataPacket.packHeader(packet_number, len(payload))

					dataPacket = dataPacketHeader + payload;

					sendPacket(dataPacket)

					print >> sys.stderr, "Packets sent %d" % packet_number

					#Sending end of stream packet		
					endPacket = StreamEndPacket.pack()

					sendPacket(endPacket);

					end_time = time.clock()
			
					print >> sys.stderr, "Time taken: %0.5f seconds" % (end_time - start_time)

		elif data[4:5] == protocol.request_packet_type:
			request_packet_header = RequestPacket.unpackHeader(data[:8])
			request_packet_payload = RequestPacket.unpackPayload(request_packet_header[3], data[8:])

			print >> sys.stderr, request_packet_header

			with open("movie.mjpeg", "rb") as file:
				for missed_packet in request_packet_payload:
					file.seek((missed_packet - 1) * 118)
					dataPayload = file.read(128)
					dataPacketHeader = DataPacket.packHeader(missed_packet, len(dataPayload))
					dataPacket = dataPacketHeader + dataPayload
					sendPacket(dataPacket)

			#Sending end of stream packet		
			endPacket = StreamEndPacket.pack()

			sendPacket(endPacket);		

					

# print >> sys.stderr, 'Start of stream packet sent.'

# sendPacket(startPacket.pack())


# tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# tcp_socket.bind(("", protocol.tcp_port))
# tcp_socket.listen(True)


# conn, addr = tcp_socket.accept()
# print 'Connection from address:', addr

# while True:
   
#     ready_socks,_,_ = select.select(socks, [], []) 
#     for sock in ready_socks:
#         data, addr = sock.recvfrom(1024) # This is will not block
#         print "Received ack:", data

# while True:
# 	try:
# 		data, server = conn.recvfrom(protocol.max_packet_size);
# 	except socket.timeout:
# 		print >> sys.stderr, 'TCP socket timed out.'
# 		break
# 	else:
# 		print >> sys.stderr, "Received ack of start of stream packet: %s" % data 

# Look for responses from all recipients
# while True:
# 	print >> sys.stderr, 'Waiting for confirmation of receipt...'

# 	try:
# 		data, server = sock.recvfrom(16);
# 	except socket.timeout:
# 		print >> sys.stderr, 'Socket timed out.'
# 		break
# 	else:
# 		print >> sys.stderr, 'Received "%s" from %s' % (data, server)
# 		print >> sys.stderr, 'Starting file transmission...'

# 		with open("movie.mjpeg", "rb") as file:
# 				byte = file.read(1)
# 				payload = bytearray()

# 				packet_number = 0

# 				while byte != "":
# 					payload.append(byte)

# 					if len(payload) == 118:
						
# 						packet_number += 1

# 						dataPacketHeader = DataPacket.packHeader(packet_number, 118)

# 						dataPacket = dataPacketHeader + payload;

# 						# print >> sys.stderr, 'Packet of length: %d was sent.' % len(dataPacket)
# 						sendPacket(dataPacket)
# 						payload = bytearray()	
					
# 					byte = file.read(1)

# 				packet_number += 1

# 				dataPacketHeader = DataPacket.packHeader(packet_number, len(payload))

# 				dataPacket = dataPacketHeader + payload;

# 				sendPacket(dataPacket)

# 				print >> sys.stderr, "Packets sent %d" % packet_number

# 		break

# #Sending end of stream packet		
# endPacket = StreamEndPacket.pack()

# sendPacket(endPacket);

# print >> sys.stderr, 'Waiting for confirmation of succesful file receipt...'

# while True:
# 	try:
# 		data, server = sock.recvfrom(1024);
# 	except socket.timeout:
# 		print >> sys.stderr, 'Socket timed out.'
# 		break
# 	else:
# 		print >> sys.stderr, 'Received "%d" bytes from %s' % (len(data), server)

# 		if (data[:3] == protocol.name):
# 			if (data[4:5] == protocol.request_packet_type):
# 				print >> sys.stderr, "Request packet received."

# 				request_packet_header = RequestPacket.unpackHeader(data[:8])
# 				request_packet_payload = RequestPacket.unpackPayload(request_packet_header[3], data[8:])

# 				print >> sys.stderr, request_packet_header

# 				with open("movie.mjpeg", "rb") as file:
# 					for missed_packet in request_packet_payload:
# 						file.seek((missed_packet - 1) * 118)
# 						dataPayload = file.read(128)
# 						dataPacketHeader = DataPacket.packHeader(missed_packet, len(dataPayload))
# 						dataPacket = dataPacketHeader + dataPayload
# 						sendPacket(dataPacket)

# 				#Sending end of stream packet		
# 				endPacket = StreamEndPacket.pack()

# 				sendPacket(endPacket);	

# 			if (data[4:5] == protocol.success_packet_type):
# 				print >> sys.stderr, "Transmission success."
# 				break
				
# 		else:
# 			print >> sys.stderr, "Invalid protocol. Packet dropped."		


# end_time = time.clock()
		
# print >> sys.stderr, "Time taken: %0.5f seconds" % (end_time - start_time)





