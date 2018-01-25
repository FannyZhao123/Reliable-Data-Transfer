# Reliable-Data-Transfer


Reliable-Data-Transfer:
	Go-Back-N and Selective Repeat versions of pipelined reliable data transfer, as well as a simple file transfer application that can transfer any file (including binary files) over the unreliable channel emulator.

How to run the program:
	--chmod 777 channel
	--chmod 777 Receiver
	--chmod 777 Sender
	--starting the Receiver: ./Receiver <protocol selector> <filename>
	--starting the channel: ./channel <max delay> <discard probability> <random seed> <verbose>
	--starting the Sender: ./Sender <protocol selector> <timeout> <filename>

Machines:
	--My program is build on ubuntu1604-006 student environment, and test on ubuntu1604-006 student environment too.

Part that completed:
	-- Receiver in Go_Back_N and Selective Repeat
	-- Sender in Go_Back_N and Selective Repeat

Dasic design ideas:
	-- Receiver: Using while loop to achive Go_Back_N or Selective Repeat to receive the message from channel socket and store them into a file.
	-- Sender: After receiving the channel_info, open the file that need to be send. Then using Go_Back_N(while loop) or Selective Repeat(mulitithread sending socket) to send packet to channel.


