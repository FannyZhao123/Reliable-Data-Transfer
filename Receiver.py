#!/usr/bin/python

import socket
import select
import time
from struct import *
import sys

#0 Data Packet
#1 Acknowledgement (ACK) Packet
#2 End-Of-Transfer (EOT) Packet (see below for details)
Data_Packet = 0
ACK_Packet = 1
EOT_Packet = 2
window_size = 10
Channel_Info = "channelInfo"
#current_seq = 1
#next_seq = 1
if_EOT = False
Receiver_Info = "recvInfo"


# r_go_back_n: function that used for receing the file
#input: filename that sotre the massage to
def r_go_back_n(filename):
	#the seq num that receiver needed
	r_seq = 1

	while True:
#		try:
#			print 'Im in the loop'
			#rlist: wait until ready for reading
			#wlist: wait until ready for writing
			print 'Running select to receive r_socket.'
			readable, writable, exceptional = select.select([r_socket], [], [])
			# All of the sockets in the readable list have incoming data buffered and available to be read

			data, address = readable[0].recvfrom((32*3)/8 + 500)
			#header in length of 12, 3 integers
			header = unpack('>III', data[:12])
			#print outfut of receiving file
			if header[0] == Data_Packet:
				print 'PKT RECV DAT {0} {1}'.format(header[1], header[2])
				payload = unpack('>{0}s'.format(header[1]-12), data[12:header[1]])

				#got expected seq, write into file
				if r_seq == header[2]:
					file_needed.write(payload[0])
					ack = pack('>III', 1, 12, r_seq)
					r_socket.sendto(ack, (address[0], address[1]))
					print 'PKT SEND ACK 12 {0}'.format(r_seq)
					r_seq += 1
				#wrong seq num
				else:
					if r_seq > header[2]:
						ack = pack('>III', 1, 12, header[2])
					else:
						ack = pack('>III', 1, 12, r_seq-1)
					r_socket.sendto(ack, (address[0], address[1]))
					if r_seq > header[2]:
						print 'PKT SEND ACK 12 {0}'.format(header[2])
					else:
						print 'PKT SEND ACK 12 {0}'.format(r_seq-1)

			elif header[0] == ACK_Packet:
				print 'PKT RECV ACK {0} {1}'.format(header[1], header[2])

			else:
				print 'PKT RECV EOT {0} {1}'.format(header[1], header[2])
				eof = pack('>III', 2, 12, 0)
				r_socket.sendto(eof, (address[0], address[1]))
				file_needed.close()
				print 'PKT SEND EOT 12 0'
				sys.exit()
#		except select.error:
#			print 'caught a error'
#			pass


#function used for receive message from SR
#input: faile name that we need put message to
def r_selective_repeat(filename):
	#need a key value pair list for storing the window
	KV_pair = {}

	current_seq = 1
	next_seq = 1
	while True:
		try:
#			print 'Im in the loop'
			#rlist: wait until ready for reading
			#wlist: wait until ready for writing
			print 'Running select to receive r_socket.'
			readable, writable, exceptional = select.select([r_socket], [], [])
			# All of the sockets in the readable list have incoming data buffered and available to be read

			data, address = readable[0].recvfrom((32*3)/8 + 500)
			#header in length of 12, 3 integers
			header = unpack('>III', data[:12])
			#print outfut of receiving file
			if header[0] == Data_Packet:
				print 'PKT RECV DAT {0} {1}'.format(header[1], header[2])
				
				if (current_seq+10 > header[2]):
					print 'writing file 2.'
					payload = unpack('>{0}s'.format(header[1]-12), data[12:header[1]])
					
					#got expected seq, write into file
					if current_seq == header[2]:
						print 'writing file 1.'
						current_seq = current_seq+1
						file_needed.write(payload[0])
					if current_seq-10 <= header[2]:
						ack = pack('>III', 1, 12, header[2])
						r_socket.sendto(ack, (address[0], address[1]))
						print 'PKT SEND ACK 12 {0}'.format(header[2])
			elif header[0] == ACK_Packet:
				print 'PKT RECV ACK {0} {1}'.format(header[1], header[2])

			else:
				print 'PKT RECV EOT {0} {1}'.format(header[1], header[2])
				eof = pack('>III', 2, 12, 0)
				r_socket.sendto(eof, (address[0], address[1]))
				file_needed.close()
				print 'PKT SEND EOT 12 0'
				sys.exit()
				
		except select.error:
			pass			


#main
#Receiver has two arguments:
#	protocol selector - 0 for Go-Back-N or 1 for Selective Repeat
#	the filename to which the transferred file is written.

#check argv
if len(sys.argv) != 3:
	sys.exit( "ERROR! Need 2 arguments for Receiver")
protocol_selector = int(sys.argv[1])
filename = sys.argv[2]

#setup the socket
print 'Reading from the receiving socket.'
r_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r_socket.bind(("0.0.0.0",0))
#open receiver info
add1 = r_socket.getsockname()[0] #hostname
add2 = r_socket.getsockname()[1] #port number
with open(Receiver_Info, 'w') as ri:
	ri.write('{0} {1}\n'.format(add1, add2))

#append teh binary file to file_needed
file_needed = open (filename, 'ab')

if(protocol_selector == 0):
	r_go_back_n(filename)
elif(protocol_selector == 1):
	r_selective_repeat(filename)
else:
	print 'ERROR! expecting either 0 or 1 for protocol_selector!'
	sys.exit()
