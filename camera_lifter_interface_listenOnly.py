#!/usr/bin/env python3

import socket
import time
import pickle


################################## UDP Socket ##################################
## Listening to console data receiver
SLU_PORT = 6666
slu_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
slu_sock.bind(("0.0.0.0", SLU_PORT))
slu_sock.setblocking(0)

## Listening on moab kopropo SBUS channel
SLU_RC_PORT = 7777
slu_rc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
slu_rc_sock.bind(("0.0.0.0", SLU_RC_PORT))
slu_rc_sock.setblocking(0)

## Publishing data to data publisher
SLU_FB_PORT = 8888
slu_fb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


###################################### Loop ##########################################


while True:

	###############################################################
	################# Get camera data from console ################
	###############################################################
	try:
		data, addr = slu_sock.recvfrom(1024)
		data = pickle.loads(data)
	except socket.error:
		pass
	else:
		print(data)

	###########################################################
	################# Get camera jog from moab ################
	###########################################################
	try:
		data, addr = slu_rc_sock.recvfrom(1024)
		data = pickle.loads(data)
	except socket.error:
		pass
	else:
		print(data)


	time.sleep(0.0001)