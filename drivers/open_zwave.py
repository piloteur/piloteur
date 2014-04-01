import os
import time
from datetime import datetime
import subprocess

def startDriver():
	
	nameCode = ["sudo","./test"]

	#p = subprocess.Popen(nameCode,stdout=subprocess.PIPE,cwd="/home/smarthome/smarthome-drivers/drivers/open-zwave/cpp/examples/linux/MinOZW")
	subprocess.call(nameCode)
	
	#while True:
		
		#a = 1
		
	"""
	while True:
                print subprocess.check_output(["echo", "Is it zwave?"])
                time.sleep(1)
	"""
	
def main():
	
	if not os.path.exists("/home/smarthome/smarthome/data/open-zwave"):
    		os.makedirs("/home/smarthome/smarthome/data/open-zwave")
	
	os.chdir("/home/smarthome/smarthome-drivers/drivers/open-zwave/cpp/examples/linux/MinOZW")
	while True:
			time.sleep(2)
			startDriver()
		



if __name__ == "__main__":
	main()


