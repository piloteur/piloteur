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

def my_callback(channel):
        motion = False
        if(GPIO.input(GPIO_PIR0)):
                motion = True
        print str(datetime.datetime.now()) + " 0 " + str(motion)
def my_callback1(channel):
        motion = False
        if(GPIO.input(GPIO_PIR1)):
                motion = True
        print str(datetime.datetime.now()) + " 1 " + str(motion)
def my_callback2(channel):
        motion = False
        if(GPIO.input(GPIO_PIR2)):
                motion = True
        print str(datetime.datetime.now()) + " 2 " + str(motion)
def my_callback3(channel):
        motion = False
        if(GPIO.input(GPIO_PIR3)):
                motion = True
        print str(datetime.datetime.now()) + " 3 " + str(motion)

GPIO.add_event_detect(GPIO_PIR0, GPIO.BOTH, callback=my_callback, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR1, GPIO.BOTH, callback=my_callback1, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR2, GPIO.BOTH, callback=my_callback2, bouncetime=200)
GPIO.add_event_detect(GPIO_PIR3, GPIO.BOTH, callback=my_callback3, bouncetime=200)

try:
        while True:
                pass

except KeyboardInterrupt:
        GPIO.cleanup()
GPIO.cleanup()
