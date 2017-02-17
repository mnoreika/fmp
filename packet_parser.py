import protocol
import sys

from packet import *

# Sends a control message using TCP
def send_message(message, tcp_socket):
	try:
		tcp_socket.send(message)
	except:
		print >> sys.stderr, "Connection closed by the sender.\n"


# Reads start of stream packet
def readStreamStartPacket(data, tcp_socket):
	global file
	global packet_number

	packet = StreamStartPacket.unpack(data)

	file_name = packet[5].split(b'\0',1)[0]
	print >> sys.stderr, 'Incoming file: %s' % file_name
	file = open(file_name + ".received", "w+b")

	# Set the total number of packets expected
	packet_number = protocol.window_size

	send_message(SuccessPacket.pack(), tcp_socket)


# Reads end of stream packet
def readStreamEndPacket(data, tcp_socket):
	packet = StreamEndPacket.unpack(data[:5])

	global expected_packet
	global packets_missing
	global number_of_packets
	global packet_number
	global file_received
	global stream_finished


	print >> sys.stderr, "# EOS #"

	# If file already received, ignore other packets
	if (file_received == True):
		send_message(SuccessPacket.pack(), tcp_socket)
		print >> sys.stderr, "Sending success packet 1"
		return

	# Determine if all packets have been received
	if (stream_finished == False and expected_packet - 1 != packet_number):
		for packet_number in range (expected_packet, packet_number + 1):
			if packet_number not in packets_missing:
				packets_missing.append(packet_number)

	stream_finished = True			

	if len(packets_missing) != 0:

		# Check if packets are missing and request the mising ones 
		print >> sys.stderr, "Missing packets: %d \n" % (len(packets_missing))

		requestPacket = RequestPacket.packHeader(len(packets_missing)) + RequestPacket.packPayload(len(packets_missing) , packets_missing)

 		send_message(requestPacket, tcp_socket)

	else:
		print >> sys.stderr, "Sending success packet: %d bytes" % len(SuccessPacket.pack())

		file_received = True

 		send_message(SuccessPacket.pack(), tcp_socket)


# Reads data packet and writes data to file
def readDataPacket(packet, data):
	file.seek(118 * (packet[3] - 1))
	file.write(data[10:(10 + packet[4])])

# Parses an incoming packet
def parsePacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	global file_received
	global stream_finished
	
	# Read start of stream packet
	if (data[4:5] == protocol.start_packet_type):
		expected_packet = 1
		packets_missing = []
		file_received = False
		stream_finished = False

		readStreamStartPacket(data, tcp_socket)

	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:10])

		# If file already received, ignore other packets
		if (file_received == True):
			send_message(SuccessPacket.pack(), tcp_socket)
			return

		readDataPacket(packet, data)

		print >> sys.stderr, "Received: %d" % packet[3]

		# Remove packet from missing list
		if (packet[3] in packets_missing):
			packets_missing.remove(packet[3])
			return

		# Add missed packets to the list	
		if (stream_finished == False):
			if expected_packet != packet[3]:
				 for packet_number in range (expected_packet, packet[3]):
				 	packets_missing.append(packet_number)

			expected_packet = packet[3] + 1


	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data, tcp_socket)
