from slu_functions import *
import time
import socket
import argparse
import json
import threading
# from SbusParser import SbusParser


############################### Arguments parser ###############################

parser = argparse.ArgumentParser(description='Run line follower')
parser.add_argument('--slu',
					help="This is device name of slu unit")

args = parser.parse_args()
slu = args.slu

if slu is None:
	print("Error: please specify slu unit")
	quit()

ser = serial.Serial(slu, timeout=0)  

################################## UDP Socket ##################################
## Listening to console data receiver
SLU_PORT = 6666
slu_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
slu_sock.bind(("0.0.0.0", SLU_PORT))
slu_sock.setblocking(0)

## Listening on moab kopropo SBUS channel
SLU_RC_PORT = 7777
slu_rc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
slu_rc_sock.bind(("0.0.0.0", SLU_PORT))
slu_rc_sock.setblocking(0)

## Publishing data to data publisher
SLU_FB_PORT = 8888
slu_fb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


################################## Parameters ###########################################

channel_trim = 1020
deadband_width = 20
speed_factor_propo = 20
speed_factor_webrtc = 10000
acceleration = 10000
loop_sleep_time = 0.05

velocity_deadband = 100
position_deadband = 100

################################### Initializeation #####################################

time.sleep(2)
ser.write(initialize().encode())
ser.write(set_drive_mode(1).encode())  # 0 means position control;  1 means velocity control
ser.write(set_velocity_absolutely(0).encode())
ser.write(set_acceleration_absolutely(acceleration).encode())


#propo_channels = SbusParser() 

first = True

####################################### Thread ########################################
prev_time = time.time()
latest_position = 0

def read_from_serial_port(ser):
	global latest_position

	while True:
		serial_fb = ser.readline().decode()
		# print(serial_fb)
		try:
			if (len(serial_fb) > 0) and (int(serial_fb) != 0):
				latest_position = int(serial_fb)
				# print("serial_fb: " + str(serial_fb) + "          len: "+ str(len(serial_fb)))
		except:
			pass


thread = threading.Thread(target=read_from_serial_port, args=(ser,), daemon=True)
thread.start()

###################################### Loop ##########################################

while True:
	
	moab_pkt = None
	webrtc_pkt = None

	####################################
	# Read packets from moab and webrtc
	####################################

	try:
		while True:
			moab_pkt, addr = slu_rc_sock.recvfrom(1024, socket.MSG_DONTWAIT)
			# pkt = data.decode()
	except:
		moab_pkt = moab_pkt

	try:
		while True:
			webrtc_pkt, addr = slu_sock.recvfrom(1024, socket.MSG_DONTWAIT)
			#print("got imu packet")
	except:
		webrtc_pkt = webrtc_pkt


	########################################
	# If bot mode is manual, run with propo
	########################################

	if moab_pkt:  ################## TO BE EDITED, the condition of moab(auto/manual) mode should be added ################

		propo_channels.parse_packet(moab_pkt)
		print(propo_channels.__dict__)
		ch3 = propo_channels.prev_ch3


		try:

			# move with right stick ch C

			if  (ch3 < channel_trim-deadband_width) or (ch3 > channel_trim+deadband_width):
				print("move")
				ser.write(set_velocity_absolutely((ch3-channel_trim) * speed_factor).encode())

			else:
				print("stay")
				ser.write(set_velocity_absolutely(0).encode())

		#######################################
		# If bot mode is auto, run with webrtc
		#######################################

	elif webrtc_pkt:
		# Decode the input from momo
		webrtc_pkt_dec = webrtc_pkt.decode()
		dec = json.loads(webrtc_pkt_dec)
		print(dec)

		# Assign velocity and position
		position_in = dec['CAM_POS']                       ############## TO BE EDITED, if format is different
		velocity_in = dec['CAM_VEL']

		try:
			#####################
			# If slider is moved
			#####################
			if  (abs(velocity_in - prev_velocity_in) > velocity_deadband) or (abs(position_in - prev_position_in) > position_deadband):

				ser.write(set_drive_mode(0).encode())

				# Set the velocity first and then move to position and wait for position control to complete

				print("move")
				ser.write(set_velocity_absolutely(velocity_in).encode())
				ser.write(set_position_absolutely(position_in).encode())
				ser.write(wait())

				ser.write(set_drive_mode(1).encode())

				#########################
				# else if stick is moved
				#########################
			elif abs(ch_right_y) > 0.05:
				
				print("move")
				ser.write(set_velocity_absolutely((-ch_right_y) * speed_factor_webrtc).encode())

			else:
				ser.write(set_velocity_absolutely(0).encode())
				print("stay")

		
		except Exception as e:
			print(e)

		prev_position_in = position_in
		prev_velocity_in = velocity_in


	# Send command for position feedback
	ser.write(get_position().encode())
	print(latest_position)

	# Send current position to data publisher
	if ( (time.time() - prev_time) > loop_sleep_time):

		# Make json
		feedback_dict = { "pos": latest_position}
		json_data = json.dumps(feedback_dict)

		# Send with udp
		slu_out_sock.sendto(json_data.encode(),(JETSON_IP,SLU_FB_PORT))

		prev_time = time.time()


	time.sleep(loop_sleep_time)


