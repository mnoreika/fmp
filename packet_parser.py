import protocol
import sys

from packet import *

def readStreamStartPacket(data, tcp_socket):
	global file
	global packet_number

	packet = StreamStartPacket.unpack(data)

	file_name = packet[5].split(b'\0',1)[0]
	print >> sys.stderr, 'Incoming file: %s' % file_name
	file = open(file_name + ".received", "w+b")

	packet_number = packet[4]

	tcp_socket.send(SuccessPacket.pack())


def readStreamEndPacket(data, tcp_socket):
	packet = StreamEndPacket.unpack(data)

	global expected_packet
	global packets_missing
	global number_of_packets
	global packet_number

	print >> sys.stderr, "# End of stream packet received #"
	print >> sys.stderr, packet

	# Determine if all packets have been received
	if (expected_packet - 1 != packet_number):
		for packet_number in range (expected_packet, packet_number + 1):
			if packet_number not in packets_missing:
				packets_missing.append(packet_number)


	if len(packets_missing) != 0:
		# Check if packets are missing and request the mising ones 
		print >> sys.stderr, "Missing packets: %d \n %s" % (len(packets_missing), packets_missing)

		requestPacket = RequestPacket.packHeader(len(packets_missing)) + RequestPacket.packPayload(len(packets_missing) , packets_missing)

		print >> sys.stderr, "Sending request packet: %d bytes" % len(requestPacket)

	 	tcp_socket.send(requestPacket)
	else:

		tcp_socket.send(SuccessPacket.pack())
 

def readDataPacket(packet, data):
	file.seek(118 * (packet[3] - 1))
	file.write(data[10:(10 + packet[4])])


def parsePacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	

	if (data[4:5] == protocol.start_packet_type):
		expected_packet = 1
		packets_missing = []

		readStreamStartPacket(data, tcp_socket)

	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:10])

		readDataPacket(packet, data)

		if (packet[3] in packets_missing):
			packets_missing.remove(packet[3])
			return;

		if expected_packet != packet[3]:
			 for packet_number in range (expected_packet, packet[3]):
			 	packets_missing.append(packet_number)
			 	print >> sys.stderr, "Missed packet: %d" % packet_number

		expected_packet = packet[3] + 1


	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data, tcp_socket)
