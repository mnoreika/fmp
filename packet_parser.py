import protocol
import sys

from packet import *

# Sends a control message using TCP
def send_message(message, tcp_socket):
	try:
		tcp_socket.sendall(message, 2048)
	except:
		print >> sys.stderr, "Connection closed by the sender.\n"

# Calculates the chunksum of window of transmission
def calculate_window_checksum(window_number):
    offset = window_number * protocol.window_size * protocol.data_payload_size 
    
    file.seek(offset)
    window_data = file.read(protocol.window_size * protocol.data_payload_size)
    
    return "%X"%(zlib.crc32(window_data, 0) & 0xFFFFFFFF)

# Reads start of stream packet
def readStreamStartPacket(data, tcp_socket):
	global file
	global last_window
	global window_size
	global last_window_size
	global file_name
	global file_checksum

	packet = StreamStartPacket.unpack(data[:279])

	file_name = packet[7].split(b'\0',1)[0]
	print >> sys.stderr, 'Incoming file: %s' % file_name
	
	# Creating a new file
	file = open(file_name + ".received", "w+b")

	# Set the paramenters of the transmission
	window_size = protocol.window_size
	last_window = packet[4]
	last_window_size = packet[5]
	file_checksum = packet[6].split(b'\0',1)[0]

	send_message(SuccessPacket.pack(current_window), tcp_socket)


# Reads end of stream packet
def readStreamEndPacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	global window_size
	global file_received
	global window_finished
	global current_window

	packet = StreamEndPacket.unpack(data[:16])

	# Ignore packet if it's not for current window
	if (packet[3] < current_window):
		# Acknoledge the success of the previous window again
		send_message(SuccessPacket.pack(current_window - 1), tcp_socket)
		return

	if (packet[3] > current_window):
		return

	# If file already received, ignore other packets
	if (file_received == True):
		# Acknoledge the success of receipt again
		send_message(SuccessPacket.pack(current_window), tcp_socket)
		return

	# Determine if all packets have been received for this window
	if (window_finished == False and expected_packet - 1 != window_size):
		for window_size in range (expected_packet, window_size + 1):
			if window_size not in packets_missing:
				packets_missing.append(window_size)

	window_finished = True	

	# Check if packets are missing and request the mising ones 
	if len(packets_missing) != 0:

		print >> sys.stderr, "Missing packets: %d" % (len(packets_missing))

		
		if (len(packets_missing) > window_size):
			# Request the whole window again
			requestPacket = RequestPacket.packHeader(0)
			send_message(requestPacket, tcp_socket)

		else:
			# Construct request packet
			requestPacket = RequestPacket.packHeader(
				len(packets_missing)) + RequestPacket.packPayload(
				len(packets_missing) , 
				packets_missing)
	 		send_message(requestPacket, tcp_socket)

	else:
		# Determine if the window is not corrupted
		computed_window_checksum = calculate_window_checksum(current_window)

		print >> sys.stderr, computed_window_checksum
		print >> sys.stderr, packet[4].split(b'\0',1)[0]

		if (computed_window_checksum == packet[4].split(b'\0',1)[0]):
			# Reset the state of the transmission
			current_window += 1
			expected_packet = 1
			packets_missing = []
			window_finished = False



			# Change the window's size for the last window
			if (current_window == last_window):
				window_size = last_window_size

			print >> sys.stderr, "ACK WINDOW %d. CHECKSUM - OK" % (current_window - 1)
	 		send_message(SuccessPacket.pack(current_window - 1), tcp_socket)	

	 	else:
	 		print >> sys.stderr, "Window is corrupted. Requesting resend..."	
			requestPacket = RequestPacket.packHeader(0)
			send_message(requestPacket, tcp_socket)

		# Determine if the received file is not corrupted
		if (current_window == last_window + 1):
			file_received = True

			computed_checksum = calculate_checksum(file_name + ".received")
		
			if (computed_checksum == file_checksum):
				print >> sys.stderr, "File has been succesfuly received."
			else:
				print >> sys.stderr, "Received file is corrupted. CRC32 check failed."	
 	

# Reads data packet and writes data to file
def writeDataPacket(packet, data, current_window):
	# Seek particular position in the file
	file.seek(current_window * protocol.window_size * protocol.data_payload_size 
		+ (packet[4] - 1) * protocol.data_payload_size)

	# Write to file according to the size of the payload speicifed in the packet's header
	file.write(data[16:(16 + packet[5])])

# Parses an incoming packet
def parsePacket(data, tcp_socket):
	global expected_packet
	global packets_missing
	global file_received
	global window_finished
	global current_window
	
	# Read start of stream packet
	if (data[4:5] == protocol.start_packet_type):
		# Re-set the transmission state
		expected_packet = 1
		packets_missing = []
		file_received = False
		window_finished = False
		current_window = 0

		readStreamStartPacket(data, tcp_socket)

	# Read data packet
	if (data[4:5] == protocol.data_packet_type):
		packet = DataPacket.unpackHeader(data[:16])

		# Ignore packet from not the current window
		if (packet[3] != current_window):
			return

		# If file already received, ignore other packets
		if (file_received == True):
			send_message(SuccessPacket.pack(current_window), tcp_socket)
			return

		# Write data to file
		writeDataPacket(packet, data, current_window)

		# Remove packet from missing list
		if (packet[4] in packets_missing):
			packets_missing.remove(packet[4])
			return

		# Add missed packets to the list	
		if (window_finished == False):
			if expected_packet != packet[4]:
				 # Determine how many packets were missed since the last received one
				 for packet_number in range (expected_packet, window_size + 1):
				 	if (packet_number not in packets_missing):
				 		packets_missing.append(packet_number)

			expected_packet = packet[4] + 1

	# Read end of stream packet
	if (data[4:5] == protocol.end_packet_type):
		readStreamEndPacket(data, tcp_socket)
