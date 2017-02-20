import struct
import protocol
import zlib


class StreamStartPacket(object):
	packet_structure = '3s c c I H H H 8s 255s' 

	def __init__ (self, file_name, packet_size, number_of_packets, 
		number_of_windows, last_window_size, file_checksum):
		self.file_name = file_name
		self.protocol_packet_type = 'S'
		self.packet_size = packet_size
		self.number_of_packets = number_of_packets
		self.number_of_windows = number_of_windows
		self.last_window_size = last_window_size
		self.file_checksum = file_checksum

	def pack(self):
		return struct.pack(
			self.packet_structure,
			protocol.name, 
			protocol.version,
			protocol.start_packet_type, 
		 	self.packet_size, 
		 	self.number_of_packets,
		 	self.number_of_windows,
		 	self.last_window_size,
		 	self.file_checksum,
		 	self.file_name)

	@staticmethod	
	def unpack(data):
		return struct.unpack(StreamStartPacket.packet_structure, data)	


class StreamEndPacket(object):
	packet_structure = '3s c c H 8s'

	@staticmethod	
	def pack(window_number, window_checksum):
		return struct.pack(
			StreamEndPacket.packet_structure,
			protocol.name, 
			protocol.version,
			protocol.end_packet_type,
			window_number,
			window_checksum)
	
	@staticmethod	
	def unpack(data):
		return struct.unpack(StreamEndPacket.packet_structure, data)		


class DataPacket(object):
	packet_structure = '3s c c H H I'

	@staticmethod
	def packHeader(packet_number, window_number, payload_size):
		return struct.pack(
			DataPacket.packet_structure,
			protocol.name, 
			protocol.version,
			protocol.data_packet_type,
			window_number,
			packet_number,
			payload_size)
	
	@staticmethod	
	def unpackHeader(data):
		return struct.unpack(DataPacket.packet_structure, data)


class RequestPacket(object):
	packet_structure = "3s c c H"

	@staticmethod
	def packHeader(number_of_packets):
		return struct.pack(
			RequestPacket.packet_structure,
			protocol.name,
			protocol.version,
			protocol.request_packet_type,
			number_of_packets)

	@staticmethod
	def unpackHeader(data):
		return struct.unpack(RequestPacket.packet_structure, data)

	@staticmethod
	def packPayload(number_of_packets, packet_list):
		return struct.pack("%dH" % number_of_packets, *packet_list)	

	@staticmethod
	def unpackPayload(number_of_packets, data):
		return struct.unpack("%dH" % number_of_packets, data)		


class SuccessPacket(object):
	packet_structure = '3s c c H'

	@staticmethod
	def pack(window_number):
		return struct.pack(
			SuccessPacket.packet_structure,
			protocol.name,
			protocol.version,
			protocol.success_packet_type,
			window_number)

	@staticmethod
	def unpack(data):
		return struct.unpack(SuccessPacket.packet_structure, data)


def calculate_checksum(file_name):
    prev_chunk = 0

    for chunk in open(file_name,"rb"):
        prev_chunk = zlib.crc32(chunk, prev_chunk)

    return "%X"%(prev_chunk & 0xFFFFFFFF)


