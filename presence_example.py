import xethru
from xethru_const import *
import sys

print "Starting XeThru sensor...",
sensor = xethru.Xethru("COM4", XTS_ID_APP_PRESENCE, detection_zone_min = 0.5, detection_zone_max = 1.3, led_mode = XT_UI_LED_MODE_FULL)
print "Ready."
print ""

if sensor.is_initialized():
	present = False
	while True:
		status = sensor.check_status()
		if 'Presence' in status:
			if present:
				if status['Presence'] == 0:
					present = False
					print "No presence detected."
			else:
				if status['Presence'] == 1:
					present = True
					print "Presence detected."
del sensor
