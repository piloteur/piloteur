#! /bin/bash

cd ~smarthome/ssh_ports

readonly COMMAND="ansible-pull -C master -i /home/pi/inventory.ini -d /home/pi/smarthome-deployment -U git@github.com:smart-home/smarthome-deployment.git"

for p in *; do
    if ! grep --quiet thermocoach $p; then continue; fi

    crontab=$(sudo -u smarthome ssh -o StrictHostKeyChecking=no -p $p pi@localhost crontab -l)
    if echo "$crontab" | grep --quiet "$COMMAND"; then
        name=$(cat $p)
        echo "################ $p" >> ~/unattended_upgrade.log
        echo "$name" >> ~/unattended_upgrade.log

        sudo -u smarthome ssh -o StrictHostKeyChecking=no -p $p pi@localhost "$COMMAND" >> ~/unattended_upgrade.log 2>&1

        echo >> ~/unattended_upgrade.log
        echo >> ~/unattended_upgrade.log
    fi
done

