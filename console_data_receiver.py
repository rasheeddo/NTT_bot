#!/usr/bin/env python3

import numpy as np
from numpy import pi
import socket
import struct
import pickle
import time
import os
import json
import argparse
from datetime import datetime
import threading

###################################### Functions ########################################
def read_socat(term):
	read = term.readline().decode()
	return read

def dateTime2String(stamp):
	timestamp_str = stamp.strftime("%Y-%m-%d_%H:%M:%S")

	return timestamp_str

def gamepad_receive_worker(GAMEPAD_PORT):

	global moab_cmd_data
	global slu_cmd_data

	prev_moab_str = 0.0
	prev_moab_thr = 0.0
	prev_cam_jog = 0.0

	print("Gamepad receiver start...")
	while True:
		with open(GAMEPAD_PORT, "rb", buffering=0) as term:
			try:
				str_buffer = read_socat(term)
				print(str_buffer)
				dec = json.loads(str_buffer)

				
				####################
				### Get Joystick ###
				####################
				moab_cmd_data["STR_VAL"] = dec["AXES"]["#00"]
				moab_cmd_data["THR_VAL"] = (-1)*dec["AXES"]["#01"]

				slu_cmd_data["CAM_JOG"] = (-1)*dec["AXES"]["#03"]


				############################
				### send to moab process ###
				############################
				## send only whenever data got changed
				if (prev_moab_str != moab_cmd_data["STR_VAL"]) or (prev_moab_thr != moab_cmd_data["THR_VAL"]):
					moab_cmd_packets = pickle.dumps(moab_cmd_data)
					moab_console_sock.sendto(moab_cmd_packets,("127.0.0.1",MOAB_CONSOLE_PORT))

				#########################################
				### send to SLU camera lifter process ###
				#########################################
				## send only whenever data got changed
				if prev_cam_jog != slu_cmd_data["CAM_JOG"]:
					slu_cmd_packets = pickle.dumps(slu_cmd_data)
					slu_sock.sendto(slu_cmd_packets,("127.0.0.1",SLU_PORT))


				prev_cam_jog = slu_cmd_data["CAM_JOG"]
				prev_moab_str = moab_cmd_data["STR_VAL"]
				prev_moab_thr = moab_cmd_data["THR_VAL"]


			except KeyboardInterrupt:
				quit()
			except Exception as e:
				print("From gamepad data receiver loop")
				print(e)
				print(str_buffer)
				print("Failed to parse")
				pass


############################### Arguments parser #############################################

parser = argparse.ArgumentParser(description='console-data-receiver')
parser.add_argument('--console_port',
					help="This is a second port generated by 01_socat.sh")
parser.add_argument('--gamepad_port',
					help="This is a second port generated by 01_socat.sh")

args = parser.parse_args()
CONSOLE_PORT = args.console_port
GAMEPAD_PORT = args.gamepad_port


if CONSOLE_PORT is None:
	print("Error: please specify console port")
	quit()

if GAMEPAD_PORT is None:
	print("Error: please specify gameapad port")
	quit()

################################### PORT and SOCKET #############################################
MOAB_CONSOLE_PORT = 5555
moab_console_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SLU_PORT = 6666
slu_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


################################# Threading ##########################################
gamepadThread = threading.Thread(target=gamepad_receive_worker, args=(GAMEPAD_PORT,), daemon=True)
gamepadThread.start()

############################################ Loop ##########################################
#AXES
# Axis0 left stick left/right
# Axis1 left stick up/down
# Axis3 right stick up/down

# SOCAT_PORT = port

####  This is a data packet that we will get from browser (as one single json)####
## { "ID" : "Logicool Gamepad F310 (STANDARD GAMEPAD Vendor: 046d Product: c21d)", 
## "TIMESTAMP" : 203376.22, "INDEX" : 0, "MAPPING" : "standard", 
## "AXES" : { "#00" : 0, "#01" : 0, "#02" : 0, "#03" : 0 }, 
## "BUTTONS" : { "#00" : 0, "#01" : 0, "#02" : 0, "#03" : 0, "#04" : 0, "#05" : 0, "#06" : 0, "#07" : 0, "#08" : 0, "#09" : 0, "#10" : 0, "#11" : 0, "#12" : 0, "#13" : 0, "#14" : 0, "#15" : 0, "#16" : 0 }, 
## "TOTAL_AXES" : 4, "TOTAL_BUTTONS" : 17, 
## "MODE": "HOLD", "TURN_DIR" : "NONE", "FORWARD" : 0, "LEFT" : 0, "RIGHT" : 0, "ARMED" : 0}

global moab_cmd_data
global slu_cmd_data

moab_cmd_data = {
					'STR_VAL' : 0.0,
					'THR_VAL' : 0.0,
}

slu_cmd_data = {
					'CAM_POS' : 0,
					'CAM_VEL' : 5000,
					'CAM_JOG' : 0.0,
}


print("Console receiver start...")
while True:

	with open(CONSOLE_PORT, "rb", buffering=0) as term:
	
		startTime = time.time()

		try:
			str_buffer = read_socat(term)
			print(str_buffer)
			dec = json.loads(str_buffer)

			####################################
			#### when press console buttons ####
			####################################

			slu_cmd_data["CAM_POS"] = dec["CAM_POS"]
			slu_cmd_data["CAM_VEL"] = dec["CAM_VEL"]



			#########################################
			### send to SLU camera lifter process ###
			#########################################
			slu_cmd_packets = pickle.dumps(slu_cmd_data)
			slu_sock.sendto(slu_cmd_packets,("127.0.0.1",SLU_PORT))



		except KeyboardInterrupt:
			quit()
		except Exception as e:
			print("From console data receiver loop")
			print(e)
			print(str_buffer)
			print("Failed to parse")
			pass

		# period = time.time() - startTime
		# print(period)
