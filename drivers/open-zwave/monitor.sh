#! /bin/bash

case "$(pidof test | wc -w)" in

0)  #echo "Restarting Zwave:     $(date)" >> /home/pi/RestartLog.txt
    #python saveLog.py
    #rm  /home/pi/open-zwave/cpp/examples/linux/MinOZW/OZW_Log.txt
    cd /home/pi/smarthome-drivers/drivers/open-zwave/open-zwave/cpp/examples/linux/MinOZW/
    ./test
	#Copy old file
    ;;
1)  #echo "ok:  $(date)" >> /home/pi/RestartLog.txt
	# all ok
    ;;
*) 
   #echo "Removed double test: $(date)" >> /home/pi/RestartLog.txt
    kill $(pidof test | awk '{print $1}')
    ;;
esac
