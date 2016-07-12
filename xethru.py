# XeThru Python Driver v1.1
#
# The MIT License (MIT)
# Copyright (c) 2016 Marius Lind Volstad
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to 
# deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
# sell copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.

from xethru_const import *
import serial
import struct
import time

class Xethru:
	def __init__(self, comport, app_id, detection_zone_min=0.5, detection_zone_max=2.5, led_mode=XT_UI_LED_MODE_OFF, response_timeout=30, verbose=False):
		self.initialized = False
		self.verbose = verbose
		try:
			self.response_timeout = response_timeout
			
			self.serial_connection = serial.Serial(comport, 115200, timeout=1)
		except serial.SerialException:
			return
			
		if not self.__reset_module():
			print "Reset module failed"
			self.serial_connection.close()
			return
			
		if app_id == XTS_ID_APP_PRESENCE:
			self.range_min = XETHRU_PRES_MIN
			self.range_max = XETHRU_PRES_MAX
			self.span_min = XETHRU_PRES_SPAN_MIN
			self.span_max = XETHRU_PRES_SPAN_MAX
		elif app_id == XTS_ID_APP_RESP:
			self.range_min = XETHRU_RESP_MIN
			self.range_max = XETHRU_RESP_MAX
			self.span_min = XETHRU_RESP_SPAN_MIN
			self.span_max = XETHRU_RESP_SPAN_MAX
		else:
			return False
			
		self.app_id = app_id
		if not self.__load_application(app_id):
			print "Load application id failed"
			self.serial_connection.close()
			return
			
		if not self.__set_led_control(led_mode):
			print "Set LED control failed"
			self.serial_connection.close()
			return
			
			
		if not self.__set_detection_zone(detection_zone_min, detection_zone_max):
			print "Set detection zone failed"
			self.serial_connection.close()
			return
			
		if not self.__set_mode(XTS_SM_RUN):
			print "Set mode failed"
			self.serial_connection.close()
			return
			
		self.initialized = True
	
	def __del__(self):
		if self.initialized:
			try:
				self.__reset_module()
			
				self.serial_connection.close()
			except serial.SerialException:
				pass
	
	def is_initialized(self):
		return self.initialized
	
	def check_status(self):
		# Check response
		if not self.initialized:
			return {}
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_APPDATA:
				if self.app_id == XTS_ID_APP_PRESENCE:
					if self.__get_integer(resp[1:5]) == XTS_ID_PRESENCE_STATUS:
						return self.__parse_presence(resp[5:])
				elif self.app_id == XTS_ID_APP_RESP:
					if self.__get_integer(resp[1:5]) == XTS_ID_RESP_STATUS:
						return self.__parse_respiration(resp[5:])
		return {}
	
	def __parse_respiration(self, data):
		respiration_status = {}
		
		respiration_status['Counter'] = self.__get_integer(data[0:4])
		respiration_status['StateCode'] = data[4] # Only the first byte in the word is valid
		respiration_status['StateData'] = self.__get_integer(data[8:12])
		respiration_status['Distance'] = self.__get_float(data[12:16])
		respiration_status['Movement'] = self.__get_float(data[16:20])
		respiration_status['SignalQuality'] = self.__get_integer(data[20:24])
		
		return respiration_status
		
	def __parse_presence(self, data):
		presence_status = {}
		
		presence_status['Presence'] = data[0] # Only the first byte in the word is valid
		presence_status['Reserved1'] = self.__get_float(data[4:8])
		presence_status['Reserved2'] = self.__get_float(data[8:12])
		presence_status['SignalQuality'] = self.__get_integer(data[12:16])
		
		return presence_status
	
	def __reset_module(self):
		# Send command
		data = [XTS_SPC_MOD_RESET]
		self.__transmit_command(data)
		
		# Wait until the module is ready
		while True:
			resp = self.__receive_response()
			if len(resp) == 5:
				if resp[0] == XTS_SPR_SYSTEM:
					if resp[1] == XTS_SPRS_READY:
						return True
			else:
				return False
				
	def __load_application(self, app_id):
		# Send command
		data = [XTS_SPC_MOD_LOADAPP]
		data = self.__append_integer(data, app_id)
		self.__transmit_command(data)
		
		# Check response
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_ACK:
				return True
		return False
		
	def __set_mode(self, mode):
		# Send command
		data = [XTS_SPC_MOD_SETMODE, mode]
		self.__transmit_command(data)
		
		# Some weird dummy data here
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_ACK:
				return True
		# Check actual response
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_ACK:
				return True
		return False
		
	def __set_led_control(self, mode):
		# Send command
		data = [XTS_SPC_MOD_SETLEDCONTROL, mode]
		self.__transmit_command(data)
		
		# Check response
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_ACK:
				return True
		return False
	
	def __set_detection_zone(self, min, max):
		# Check and correct limits
		if min < self.range_min:
			min = self.range_min
		elif min > (self.range_max - self.span_min):
			min = self.range_max - self.span_min
		
		if max > (min + self.range_max):
			max = min + self.range_max
		if max > self.range_max:
			max = self.range_max
		elif max < (min + self.span_min):
			max = min + self.span_min
			
		# Send command
		data = [XTS_SPC_APPCOMMAND, XTS_SPCA_SET]
		data = self.__append_integer(data, XTS_ID_DETECTION_ZONE)
		data = self.__append_float(data, min)
		data = self.__append_float(data, max)
		self.__transmit_command(data)
		
		# Check response
		resp = self.__receive_response()
		if len(resp) > 0:
			if resp[0] == XTS_SPR_ACK:
				return True
		return False
		
	def __transmit_command(self, data):
		self.__add_break_characters(data, XETHRU_ESC)
		self.__add_break_characters(data, XETHRU_START)
		self.__add_break_characters(data, XETHRU_END)
				
		data = [XETHRU_START] + data
		data.append(self.__calculate_checksum(data))
		data.append(XETHRU_END)
		
		if self.verbose:
			prt = "Transmitting: "
			for ch in data:
				prt = prt + hex(ch) + " "
			print prt
		
		self.serial_connection.write(bytearray(data))
	
	def __receive_response(self):
		packet_timeout = time.time() + self.response_timeout
		packet_start = False
		packet_end = False
		data = []
		
		while not packet_start:
			if time.time() > packet_timeout: 
				return [] # Timed out
				
			char = self.serial_connection.read(1)
			if len(char) == 0:
				continue
			byte = ord(char)
			
			if byte == XETHRU_START:
				packet_start = True
				data.append(byte)
		
		break_received = False
		while not packet_end:
			if time.time() > packet_timeout: 
				return [] # Timed out
			
			char = self.serial_connection.read(1)
			if len(char) == 0:
				continue
			byte = ord(char)
			
			if break_received:
				data.append(byte)
				break_received = False
			elif byte == XETHRU_ESC:
				break_received = True
			elif byte == XETHRU_END:
				packet_end = True
			else:
				data.append(byte)
				
		if self.__calculate_checksum(data) != 0:
			return [] # Checksum does not match
		
		if self.verbose:
			prt = "Received: "
			for ch in data:
				prt = prt + hex(ch) + " "
			print prt
			
		return data[1:len(data)-1]

	def __append_integer(self, data, value):
		for i in range(4):
			data.append((value>>(i*8))&0xFF)
		return data
			
	def __append_float(self, data, value):
		float = struct.pack('f', value)
		for i in range(4):
			data.append(ord(float[i]))
		return data
		
	def __get_integer(self, data):
		return (data[3]<<24) + (data[2]<<16) + (data[1]<<8) + data[0]
			
	def __get_float(self, data):
		return struct.unpack('f', chr(data[0]) + chr(data[1]) + chr(data[2]) + chr(data[3]))[0]
		
	def __add_break_characters(self, data, flag):
		i = 0
		try:
			while i < len(data):
				i = data[i:].index(flag)
				data.insert(i, XETHRU_ESC)
				i = i + 1
		except ValueError:
			pass
		
		return data

	def __calculate_checksum(self, data):
		sum = 0
		for byte in data:
			sum = sum ^ byte
		
		return sum