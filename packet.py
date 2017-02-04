import struct

protocol_name = 'MCAST'
protocol_version = 1
start_packet_type = 'S'
end_packet_type = 'E'
data_packet_type = 'D'


class StreamStartPacket(object):
	protocol_name = 'MCAST'
	protocol_version = 1
	packet_structure = '5s B c L L 20s' 

	def __init__ (self, file_name, packet_size, number_of_packets):
		self.file_name = file_name
		self.protocol_packet_type = 'S'
		self.packet_size = packet_size
		self.number_of_packets = number_of_packets

	def pack(self):
		return struct.pack(
			self.packet_structure,
			protocol_name, 
			protocol_version,
			self.protocol_packet_type, 
		 	self.packet_size, 
		 	self.number_of_packets,
		 	self.file_name)

	@staticmethod	
	def unpack(data):
		return struct.unpack(StreamStartPacket.packet_structure, data)	


class StreamEndPacket(object):

	def __init__ (self):
		self.payload = "EOF"


class DataPacket(object):

	def __init__ (self, header, payload):
		self.header = header
		self.payload = payload



