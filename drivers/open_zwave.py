import os
import time
from datetime import datetime
import subprocess

def startDriver():
	
	nameCode = "./test"
	p = subprocess.Popen(nameCode,stdout=subprocess.PIPE,cwd="/home/smarthome/smarthome-drivers/drivers/open-zwave/cpp/examples/linux/MinOZW")
	
	while True:
		#line = p.stdout.readline().rstrip()
		#if not line: break
		#print line
		a = 1
		#if p.returncode != None:
			#print "Exiti ng-------------------------"
			#break
	
def main():
	
	if not os.path.exists("/home/smarthome/smarthome/data/open-zwave"):
    		os.makedirs("/home/smarthome/smarthome/data/open-zwave")
	
	while True:
			time.sleep(2)
			startDriver()
		



if __name__ == "__main__":
	main()


