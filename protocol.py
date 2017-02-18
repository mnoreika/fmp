name = 'FMP'
version = '1'

multicast_ip = '228.5.6.7'
multicast_group = (multicast_ip, 8889)
server_address = ('', 8889)

tcp_ip = '127.0.0.1'
tcp_port = 9999

max_packet_size = 1024
data_payload_size = 118

window_size = 400

transmission_delay = 0.000001

start_packet_type = 'S'
end_packet_type = 'E'
data_packet_type = 'D'
request_packet_type = 'R'
success_packet_type = 'K'

socket_timeout = 0.2
time_to_live = 1