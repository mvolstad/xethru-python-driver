import xethru
from xethru_const import *
import sys

print "Starting XeThru sensor...",
sensor = xethru.Xethru("COM4", XTS_ID_APP_RESP, detection_zone_min = 0.5, detection_zone_max = 0.7, led_mode = XT_UI_LED_MODE_FULL)
print "Ready."
print ""

if sensor.is_initialized():
	state = 0
	while True:
		status = sensor.check_status()
		if 'StateCode' in status:
			if status['StateCode'] == XTS_VAL_RESP_STATE_BREATHING:
				print "Breathing at " + str(status['StateData']) + "RPM (%.2fmm)." % status['Movement']
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
del sensor
