import struct

protocol_name = 'FMP'
protocol_version = '1'
start_packet_type = 'S'
end_packet_type = 'E'
data_packet_type = 'D'


class StreamStartPacket(object):
	protocol_name = 'FMP'
	protocol_version = 1
	packet_structure = '3s c c L L 20s' 

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
	packet_structure = '3s c c'

	@staticmethod	
	def pack():
		return struct.pack(
			StreamEndPacket.packet_structure,
			protocol_name, 
			protocol_version,
			end_packet_type)
	
	@staticmethod	
	def unpack(data):
		return struct.unpack(StreamEndPacket.packet_structure, data)		


class DataPacket(object):
	packet_structure = '3s c c H H'

	@staticmethod
	def packHeader(packet_number, payload_size):
		return struct.pack(
			DataPacket.packet_structure,
			protocol_name, 
			protocol_version,
			data_packet_type,
			packet_number,
			payload_size)
	
	@staticmethod	
	def unpackHeader(data):
		return struct.unpack(DataPacket.packet_structure, data)




