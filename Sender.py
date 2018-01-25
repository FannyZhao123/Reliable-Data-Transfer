#!/usr/bin/python

import sys
import struct
import thread
import time
import socket
import select
import signal
import threading
from struct import *

#0 Data Packet
#1 Acknowledgement (ACK) Packet
#2 End-Of-Transfer (EOT) Packet (see below for details)
Data_Packet = 0
ACK_Packet = 1
EOT_Packet = 2
Channel_Info = "channelInfo"


def s_go_back_n (filename, timeout, channel_info):
	current_seq = 1
	next_seq = 1
	pcks_list = []
	#an handler for the timeout
	def handler(signum, frame):
		#signal.setitimer(which, seconds[, interval]
		signal.setitimer(signal.ITIMER_REAL, timeout, 1)
		i = current_seq
		while i < next_seq:
			s_socket.sendto(pcks_list[i-1], (channel_info[0], channel_info[1]))
			temp = pcks_list[i-1]
			h = unpack('>III', temp[:12])
			if h[0] == Data_Packet:
				print 'PKT SEND DTA {0} {1}'.format(h[1], h[2])
			elif h[0] == ACK_Packet:
				print 'PKT SEND ACK {0} {1}'.format(h[1], h[2])
			else:
				print 'PKT SEND EOT {0} {1}'.format(h[1], h[2])
			i += 1
	
	if_EOT = False

	signal.signal(signal.SIGALRM, handler)

	#looping for waiting for ACKs
	while True:
		try:
#			print 'Im in the loop'
			#rlist: wait until ready for reading
			#wlist: wait until ready for writing
			readable, writable, exceptional = select.select([s_socket], [], [], 0.00000000000001)
			# All of the sockets in the readable list have incoming data buffered and available to be read

#			print 'Im before the len(readable) == 1, len(readable) = {0}'.format(len(readable))
			if len(readable)-1==0:
				print 'Running select to receive data.'
#				print 'Im in the len(readable) == 1'
				data, address = readable[0].recvfrom((32*3)/8)
				#header in length of 12, 3 integers
				header = unpack('>III', data[:12])

#				print 'header[0]: ' +str(header[0])

				if header[0] == Data_Packet:
					print 'PKT RECV DTA {0} {1}'.format(header[1], header[2])
				elif header[0] == ACK_Packet:
					print 'PKT RECV ACK {0} {1}'.format(header[1], header[2])
					#if the packet sending contain the need seqnum
					#then we need to set the timer
					if header[2] == current_seq:
						signal.setitimer(signal.ITIMER_REAL, timeout, 1)
						current_seq  = header[2]+1 
				else:
					print 'PKT RECV EOT {0} {1}'.format(header[1], header[2])
					sys.exit()
#				print 'len(readable) == {0}'.format(len(readable))
		except select.error:
			continue

		#send the payload of the file
#		print 'next_seq: ' + str(next_seq)
#		print 'current_seq: ' + str(current_seq)
#		print '{0}'.format(if_EOT)
		temp_check = file_needed.closed

		if (current_seq+10 > next_seq) and temp_check==False:
#			print 'current_seq + window_size > next_seq'
			#check if the file still open
#			if not file_needed.closed:
#			print 'file didnt close'
			payload = file_needed.read(500)

			
			#if there is something in the payload
			#ie. data packet 
			l = len(payload)
			if l != 0:
				pack_format = '>III{0}s'.format(l)
				packet_length = calcsize(pack_format)
				packet = pack(pack_format, Data_Packet, packet_length, next_seq, payload)
				#append packet
				pcks_list.append(packet)
				#send socket
#				print "chennel:" + channel_info
				s_socket.sendto(packet, (channel_info[0], channel_info[1]))
				print 'PKT SEND DAT {0} {1}'.format(packet_length, next_seq)

				#check if there is time out 
				if next_seq == current_seq:
					signal.setitimer(signal.ITIMER_REAL, timeout, 1)
				next_seq += 1

			#if there is nothing in payload
			else:
				file_needed.close()

		elif if_EOT == False and next_seq == current_seq:
#			print 'next_seq == current_seq'
#			if if_EOT == False:
			#timer end right now
			signal.setitimer(signal.ITIMER_REAL, 0)
			if_EOT = True
			#eot packet only has header
			eof = pack('>III', 2, 12, 0)
			s_socket.sendto(eof, (channel_info[0], channel_info[1]))
			print 'PKT SEND EOT 12 0'
##end of Go-Back_N


#function that use selective_repeat protrcal to send message
#input: filename, timeout
def s_selective_repeat(filename, timeout, channel_info):
	#need a array to check if acks arrived
	ack_array = []	
	current_seq = 1
	next_seq = 1
	if_EOT = False

	#an handler for the timeout
	def handler(signum, frame):
		#signal.setitimer(which, seconds[, interval]
		signal.setitimer(signal.ITIMER_REAL, timeout, 1)
		i = current_seq
		while i < next_seq:
			s_socket.sendto(pcks_list[i-1], (channel_info[0], channel_info[1]))
			i += 1


	#need a timeout for each socket
#	s_socket.setitimer(timeout)
	s_socket.settimeout(timeout)

	#k-V pair of seg and pkt has been send
	send = {}
#	arrived = {}
	arrived = []
	thread_list = []

	while True:
		#check where did acks received to
		l = len(ack_array)
		if 0<l:
			for i in range(l):
				if current_seq in ack_array:
					ack_array.remove(current_seq)
					current_seq = current_seq + 1
				##
#				else:
#					current_seq = current_seq + 1
		t_check = file_needed.closed 
		if t_check== False and (current_seq>next_seq-10):
#			print 'current_seq + window_size > next_seq'
			#check if the file still open
#			if not file_needed.closed:
#			print 'file didnt close'
			payload = file_needed.read(500)
			l = len(payload)

			#if there is nothing in payload
			if l == 0:
					file_needed.close()

			#if there is something in the payload
			#ie. data packet 
			else:
				
				pack_format = '>III{0}s'.format(l)
				packet_length = calcsize(pack_format)
				packet = pack(pack_format, Data_Packet, packet_length, next_seq, payload)
#				s_socket.sendto(packet, (channel_info[0], channel_info[1]))


				#sending s_socket function
				def s_socket_sending(packet, packet_length, seq):
					s_socket.sendto(packet, (channel_info[0], channel_info[1]))
					print 'PKT SEND DAT {0} {1}'.format(packet_length, seq)
					arrived.append(seq)
			#		print 'seq: ' + str(seq)
					send[seq] = packet
					while True:
						try:
							data, address = s_socket.recvfrom(32*3/8)
							header = unpack('>III', data[:12])
							if header[0] == Data_Packet:
								print 'PKT RECV DTA {0} {1}'.format(header[1], header[2])
							elif header[0] == ACK_Packet:
								print 'PKT RECV ACK {0} {1}'.format(header[1], header[2])
							else:
								print 'PKT RECV EOT {0} {1}'.format(header[1], header[2])
			#					print 'line 182'
			#					sys.exit()
							ack_array.append(seq)
							arrived.remove(header[2])
						except:
			#				print 'packet did not send successfully, try again.'
							if len(arrived) == 0:
			#					print 'here'
			#					print 'line 190'
								if_EOT = True
								sys.exit()
			#					print 'there'
							t = arrived[0]
							s_socket.sendto( send[t], (channel_info[0], channel_info[1]))
							p = send[t]
							header = unpack('>III', p[:12])
							if header[0] == Data_Packet:
								print 'PKT SEND DTA {0} {1}'.format(header[1], header[2])
							elif header[0] == ACK_Packet:
								print 'PKT SEDN ACK {0} {1}'.format(header[1], header[2])
							else:
								print 'PKT SEND EOT {0} {1}'.format(header[1], header[2])
							continue

				#using multithread
				#thread.start_new_thread(function, args[, kwargs])
#				thread.start_new_thread(s_socket_sending, (packet, packet_length, next_seq))
				single_thread = threading.Thread(target = s_socket_sending, args = (packet, packet_length, next_seq))
                next_seq = next_seq +1

                print 'Start new thread to send s_socket.'
                single_thread.start()
                #put the started thread in to list
                thread_list.append(single_thread)
                

#		print 'next_seq == current_seq'
#		if if_EOT == False:
		#timer end right now
#		signal.setitimer(signal.ITIMER_REAL, 0)

		if_EOT = True
		for single_thread in thread_list:
			single_thread.join()
		#eof packet only has header
		eof = pack('>III', 2, 12, 0)
		s_socket.sendto(eof, (channel_info[0], channel_info[1]))
		print 'PKT SEND EOT 12 0' 
		s_socket.setblocking(True)
		data, address = s_socket.recvfrom(32*3/8)
		header = unpack('>III', data[:12])
		if header[0] == Data_Packet:
			print 'PKT RECV DTA {0} {1}'.format(header[1], header[2])
		elif header[0] == ACK_Packet:
			print 'PKT RECV ACK {0} {1}'.format(header[1], header[2])
		else:
			print 'PKT RECV EOT {0} {1}'.format(header[1], header[2])
#			print 'line 263'
			sys.exit()
##end of SR


#main
#Sender has 3 argument
#	protocol selector - 0 for Go-Back-N or 1 for Selective Repeat
#	the value of a timeout in milliseconds
#	the filename to be transferred. 
if len(sys.argv) != 4:
	sys.exit( "ERROR! Need 3 arguments for Sender")

protocol_selector = int(sys.argv[1])
#from milliseconds to seconds
timeout = int(sys.argv[2])/1000.0
filename = sys.argv[3]


#function that used for reading from channelInfo, needed for both dbn and sr
#input: NA
#output: channel_info  
def read_from_channel():
	#try to read from channel 10 times
	count = 0
	while count < 10:
		try: 
			with open(Channel_Info, 'r') as ci:
				lines = ci.readline().split()
				#IP address (or hostname) and port number
				#separated by space.
				channel_info = (lines[0], int(lines[1]))
				#check if channel info is in same dire
				if 'channel_info' not in locals():
					raise SystemExit('Error! fail to read channel file!')
				break
		#other wise there is a I/O error
		except IOError:
			print "Waiting for channel..."
			time.sleep(20)
			pass
		count += 1
	return channel_info
channel_info = read_from_channel()
s_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#read teh binary file to file_needed
file_needed = open (filename, 'rb')	


if(protocol_selector == 0):
	s_go_back_n(filename, timeout, channel_info)
elif(protocol_selector == 1):
	s_selective_repeat(filename, timeout, channel_info)
else:
	print 'ERROR! expecting either 0 or 1 for protocol_selector!'
	sys.exit()

