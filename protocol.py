name = 'FMP'
version = '1'

multicast_ip = '228.5.6.7'
multicast_group = (multicast_ip, 8888)
server_address = ('', 8888)

start_packet_type = 'S'
end_packet_type = 'E'
data_packet_type = 'D'
request_packet_type = 'R'
success_packet_type = 'K'

socket_timeout = 0.2
time_to_live = 1