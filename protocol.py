name = 'FMP'
version = '1'

multicast_ip = '228.5.6.7'
multicast_group = (multicast_ip, 8889)
server_address = ('', 8889)

tcp_ip = '127.0.0.1'
tcp_port = 9999

data_payload_size = 20000
window_size = 800

udp_buffer = data_payload_size + 2048
tcp_buffer = 2048

transmission_delay = 0

start_packet_type = 'S'
end_packet_type = 'E'
data_packet_type = 'D'
request_packet_type = 'R'
success_packet_type = 'K'

socket_timeout = 0.2
time_to_live = 1

read_timeout = 0.5