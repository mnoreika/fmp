import protocol
import sys
import hashlib

from packet import *


# Sends a control message using TCP
def send_message(message, tcp_socket):
	try:
		tcp_socket.sendall(message, 2048)
	except:
		print >> sys.stderr, "Connection closed by the sender.\n"

def calculate_window_checksum(window_number):
    offset = window_number * protocol.window_size * protocol.data_payload_size 
    
    file.seek(offset)
    window_data = file.read(protocol.window_size * protocol.data_payload_size)
    
    return "%X"%(zlib.crc32(window_data, 0) & 0xFFFFFFFF)

# Reads start of stream packet
def readStreamStartPacket(data, tcp_socket):
	global file
	global total_packet_number
	global last_window
	global window_size
	global last_window_size
	global file_name
	global file_checksum

	packet = StreamStartPacket.unpack(data[:281])

	file_name = packet[8].split(b'\0',1)[0]
	print >> sys.stderr, 'Incoming file: %s' % file_name
	file = open(file_name + ".received", "w+b")

	# Set the total number of packets expected
	total_window_size = packet[4]

	window_size = protocol.window_size

	last_window = packet[5]

	last_window_size = packet[6]

	file_checksum = packet[7].split(b'\0',1)[0]

	send_message(SuccessPacket.pack(current_window), tcp_socket)


# Reads end of stream packet
def readStreamEndPacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	global number_of_packets
	global window_size
	global file_received
	global window_finished
	global current_window
	global last_window
	global last_window_size
	global file_hash
	global total
	global file_checksum

	packet = StreamEndPacket.unpack(data[:16])

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

		if (len(packets_missing) > window_size):
			requestPacket = RequestPacket.packHeader(0)
			send_message(requestPacket, tcp_socket)
		else:
			requestPacket = RequestPacket.packHeader(len(packets_missing)) + RequestPacket.packPayload(len(packets_missing) , packets_missing)

	 		send_message(requestPacket, tcp_socket)

	else:
		print >> sys.stderr, "Sending success packet: %d bytes" % len(SuccessPacket.pack(current_window))

		if (current_window == last_window):
			file_received = True
			print >> sys.stderr, file_name

			computed_checksum = calculate_checksum(file_name + ".received")
	
			if (computed_checksum == file_checksum):
				send_message(SuccessPacket.pack(current_window), tcp_socket)
				print >> sys.stderr, "File has been succesfuly received."
			else:
				print >> sys.stderr, "Received file is corrupted. CRC32 check failed."

		# Determine if the window is not corrupted
		computed_window_checksum = calculate_window_checksum(current_window)


		if (computed_window_checksum == packet[4].split(b'\0',1)[0]):
			current_window += 1

			expected_packet = 1
			packets_missing = []
			window_finished = False

			if (current_window == last_window):
				window_size = last_window_size

			print >> sys.stderr, "ACK WINDOW %d. CHECKSUM - OK" % (current_window - 1)
	 		send_message(SuccessPacket.pack(current_window - 1), tcp_socket)	

	 	else:
	 		print >> sys.stderr, "Window is corrupted. Requesting resend..."	
			requestPacket = RequestPacket.packHeader(0)
			send_message(requestPacket, tcp_socket)
 	

# Reads data packet and writes data to file
def readDataPacket(packet, data, current_window):
	file.seek(current_window * protocol.window_size * protocol.data_payload_size 
		+ (packet[4] - 1) * protocol.data_payload_size)
	file.write(data[16:(16 + packet[5])])

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
		packet = DataPacket.unpackHeader(data[:16])

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
