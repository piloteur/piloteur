import os
import time
from datetime import datetime

def main():
	


	count = 0
	lineNo = -1
	i = 0
	nameCode = "./test"

	for line in os.popen("ps "):
        	if(line.find(nameCode) > -1):
                     #os.command("echo \"OK\" >> RestartLog.txt")
                     count = count + 1

                     lineNo = i
     		i = i + 1


	#count = 1 means all ok
	if(count == 0):

       		#os.system("echo" + " \"" + str(datetime.now())  +  " Starting Code\" >> RestartLog.txt")
		os.chdir("/home/smarthome/smarthome-drivers/drivers/open-zwave/open-zwave/cpp/examples/linux/MinOZW")
        	os.system(nameCode)

	if(count > 1):

        	os.system("sudo pkill " + nameCode )
        	#os.system("echo" + " \"" + str(datetime.now())  + " Killed Duplicate\" >> RestartLog.txt")
		os.chdir("/home/smarthome/smarthome-drivers/drivers/open-zwave/open-zwave/cpp/examples/linux/MinOZW")
        	os.system(nameCode)

	#Since Pi code ensures this code will always run

	time.sleep( 600 )


if __name__ == "__main__":
	main()


