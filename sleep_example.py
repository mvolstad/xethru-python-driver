import xethru
from xethru_const import *
import sys

print "Starting XeThru sensor...",
sensor = xethru.Xethru("/dev/ttyACM0", XTS_ID_APP_SLEEP, reconfigure_sensor = True, detection_zone_min = 0.7, detection_zone_max = 1.8, led_mode = XT_UI_LED_MODE_OFF, sensitivity=7, output_format = XTS_SACR_ID_BASEBAND_OUTPUT_OFF, verbose = False)
print "Ready."
print ""

if sensor.is_initialized():
	state = 0
	while True:
		status = sensor.check_status()
		if 'Type' in status:
			if status['Type'] == XTS_ID_SLEEP_STATUS:
				if status['StateCode'] == XTS_VAL_RESP_STATE_BREATHING:
					print "Breathing at " + str(status['StateData']) + " RPM."
					print "Distance: " + str(status['Distance']) + "m."
					print "Signal Quality: " + str(status['SignalQuality']) + "."
					print "Movement slow: " + str(status['MovementSlow']) + "."
					print "Movement fast: " + str(status['MovementFast']) + "."
					print ""
					pass
				elif status['StateCode'] == XTS_VAL_RESP_STATE_MOVEMENT:
					print "Movement"
					pass
				elif status['StateCode'] == XTS_VAL_RESP_STATE_MOVEMENT_TRACKING:
					print "Movement tracking"
					pass
				elif status['StateCode'] == XTS_VAL_RESP_STATE_NO_MOVEMENT:
					print "No movement"
					pass
				elif status['StateCode'] == XTS_VAL_RESP_STATE_INTIALIZING:
					print "Initializing"
					pass
				else:
					print "Unknown"
					pass
			elif status['Type'] == XTS_ID_BASEBAND_IQ:
				print status
			elif status['Type'] == XTS_ID_BASEBAND_AMPLITUDE_PHASE:
				print status
del sensor
