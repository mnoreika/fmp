import protocol
import sys

from packet import *


# Sends a control message using TCP
def send_message(message, tcp_socket):
	try:
		tcp_socket.sendall(message, 2048)
	except:
		print >> sys.stderr, "Connection closed by the sender.\n"


# Reads start of stream packet
def readStreamStartPacket(data, tcp_socket):
	global file
	global total_packet_number
	global last_window
	global window_size
	global last_window_size

	packet = StreamStartPacket.unpack(data[:34])

	file_name = packet[7].split(b'\0',1)[0]
	print >> sys.stderr, 'Incoming file: %s' % file_name
	file = open(file_name + ".received", "w+b")

	# Set the total number of packets expected
	total_window_size = packet[4]

	window_size = protocol.window_size

	last_window = packet[5]

	last_window_size = packet[6]

	send_message(SuccessPacket.pack(current_window), tcp_socket)


# Reads end of stream packet
def readStreamEndPacket(data, tcp_socket):
	packet = StreamEndPacket.unpack(data[:8])

	global expected_packet
	global packets_missing
	global number_of_packets
	global window_size
	global file_received
	global window_finished
	global current_window
	global last_window
	global last_window_size

	global total

	if (packet[3] < current_window):
		send_message(SuccessPacket.pack(current_window - 1), tcp_socket)
		return

	if (packet[3] > current_window):
		return

	print >> sys.stderr, "# EOS of Window  %d #" % packet[3] 

	# If file already received, ignore other packets
	if (file_received == True):
		send_message(SuccessPacket.pack(current_window), tcp_socket)
		print >> sys.stderr, "Sending success packet 1"
		return

	# Determine if all packets have been received
	if (window_finished == False and expected_packet - 1 != window_size):
		for window_size in range (expected_packet, window_size + 1):
			if window_size not in packets_missing:
				packets_missing.append(window_size)

	window_finished = True			

	if len(packets_missing) != 0:

		# Check if packets are missing and request the mising ones 
		print >> sys.stderr, "Missing packets: %d \n" % (len(packets_missing))

		if (len(packets_missing) > 400):
			request_list = packets_missing[0: 400]
			requestPacket = RequestPacket.packHeader(len(request_list)) + RequestPacket.packPayload(len(request_list) , request_list)
			send_message(requestPacket, tcp_socket)
		else:
			requestPacket = RequestPacket.packHeader(len(packets_missing)) + RequestPacket.packPayload(len(packets_missing) , packets_missing)

	 		send_message(requestPacket, tcp_socket)

	else:
		print >> sys.stderr, "Sending success packet: %d bytes" % len(SuccessPacket.pack(current_window))

		

		if (current_window == last_window):
			file_received = True
			print >> sys.stderr, "Packets received: %d" % total 
			print >> sys.stderr, "File succesfuly received."

		current_window += 1

		expected_packet = 1
		packets_missing = []
		window_finished = False

		if (current_window == last_window):
			window_size = last_window_size

		print >> sys.stderr, "ACK WINDOW %d" % (current_window - 1)
 		send_message(SuccessPacket.pack(current_window - 1), tcp_socket)	

		
 	

# Reads data packet and writes data to file
def readDataPacket(packet, data, current_window):
	file.seek(current_window * protocol.window_size * protocol.data_payload_size + (packet[4] - 1) * protocol.data_payload_size)
	file.write(data[12:(12 + packet[5])])

# Parses an incoming packet
def parsePacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	global file_received
	global window_finished
	global current_window
	global total
	
	# Read start of stream packet
	if (data[4:5] == protocol.start_packet_type):
		expected_packet = 1
		packets_missing = []
		file_received = False
		window_finished = False
		current_window = 0
		total = 0

		readStreamStartPacket(data, tcp_socket)

	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:12])

		if (packet[3] != current_window):
			return

		# If file already received, ignore other packets
		if (file_received == True):
			send_message(SuccessPacket.pack(current_window), tcp_socket)
			return

		readDataPacket(packet, data, current_window)
		total += 1

		# Remove packet from missing list
		if (packet[4] in packets_missing):
			packets_missing.remove(packet[4])
			return

		# Add missed packets to the list	
		if (window_finished == False):
			if expected_packet != packet[4]:
				 for packet_number in range (expected_packet, packet[4]):
				 	packets_missing.append(packet_number)

			expected_packet = packet[4] + 1


	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data, tcp_socket)
