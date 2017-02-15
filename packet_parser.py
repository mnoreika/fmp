import protocol
import sys

from packet import *

def readStreamStartPacket(data, tcp_socket):
	global file
	
	packet = StreamStartPacket.unpack(data)

	print >> sys.stderr, packet

	file_name = packet[5].split(b'\0',1)[0]
	print >> sys.stderr, 'File name: %s' % file_name

	file = open(file_name + ".received", "w+b")

	success_packet = SuccessPacket.pack()

	tcp_socket.send(success_packet)


def readStreamEndPacket(data, tcp_socket):
	packet = StreamEndPacket.unpack(data)

	print >> sys.stderr, "# End of stream packet received #"
	print >> sys.stderr, packet

	global packet_number
	print >> sys.stderr, "Packets received: %d\n" % (packet_number - len(packets_missed))

	if (len(packets_missed) != 0):
		# Check if packets are missing and request the mising ones 
		print >> sys.stderr, "Packets missed: %d \n %s" % (len(packets_missed), packets_missed)

		requestPacket = RequestPacket.packHeader(len(packets_missed)) + RequestPacket.packPayload(len(packets_missed) , packets_missed)

		print >> sys.stderr, "Sending request packet: %d bytes" % len(requestPacket)

	 	tcp_socket.send(requestPacket)
	else:
		success_packet = SuccessPacket.pack()

		print >> sys.stderr, "Sending success packet: %d bytes" % len (success_packet)

		tcp_socket.send(success_packet)
 

def readDataPacket(packet, data):
	file.seek(118 * (packet[3] - 1))

	file.write(data[10:(10 + packet[4])])


def parsePacket(data, tcp_socket):
	global packet_number
	global packets_missed

	if (data[4:5] == protocol.start_packet_type):
		print >> sys.stderr, '\n# Start of transmission packet received #'

		packet_number = 0

		packets_missed = []

		readStreamStartPacket(data, tcp_socket)

	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:10])

		packet_number += 1

		if (packet[3] in packets_missed):
			packets_missed.remove(packet[3])

		elif (packet_number != packet[3]):
			packets_missed.append(packet_number)

			packet_number += 1


		readDataPacket(packet, data)

	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data, tcp_socket)
