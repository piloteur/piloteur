import os
import time

def main():
	
	os.system("/home/pi/smarthome-drivers/drivers/open-zwave/./monitor.sh")
	time.sleep(600)

if __name__ == "__main__":
	main()


