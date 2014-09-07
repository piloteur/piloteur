#! /bin/bash

cd ~smarthome/ssh_ports

readonly COMMAND="ansible-pull.sh"

for p in *; do
    if ! grep --quiet thermocoach $p; then continue; fi

    crontab=$(sudo -u smarthome ssh -o StrictHostKeyChecking=no -p $p pi@localhost crontab -l)
    if ! (echo "$crontab" | grep --quiet "$COMMAND"); then
        name=$(cat $p)
        echo "################ $p" >> ~/unattended_upgrade.log
        echo "$name" >> ~/unattended_upgrade.log

        echo >> ~/unattended_upgrade.log
    fi
done

