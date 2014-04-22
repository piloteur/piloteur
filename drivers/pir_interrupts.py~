import RPi.GPIO as GPIO
import datetime
import time

GPIO.setmode(GPIO.BCM)
GPIO_PIR0 = 23
GPIO_PIR1 = 25
GPIO_PIR2 = 18
GPIO_PIR3 = 4 

GPIO.setup(GPIO_PIR0, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIR1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIR2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIR3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

motion0 = False
motion1 = False
motion2 = False
motion3 = False

def my_callback(channel):
	global motion0
	motion0 = not motion0
	print str(datetime.datetime.now()) + " 0 " + str(motion0)
def my_callback1(channel):
	global motion1
	motion1 = not motion1
	print str(datetime.datetime.now()) + " 1 " + str(motion1)
def my_callback2(channel):
	global motion2
	motion2 = not motion2
	print str(datetime.datetime.now()) + " 2 " + str(motion2)
def my_callback3(channel):
	global motion3
	motion3 = not motion3
	print str(datetime.datetime.now()) + " 3 " + str(motion3)

GPIO.add_event_detect(GPIO_PIR0, GPIO.RISING, callback=my_callback, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR1, GPIO.RISING, callback=my_callback1, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR2, GPIO.RISING, callback=my_callback2, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR3, GPIO.RISING, callback=my_callback3, bouncetime=200)

try:
	while True:
		pass

except KeyboardInterrupt:
	GPIO.cleanup()
GPIO.cleanup()

