#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import textwrap
import os.path
import os
import subprocess
import time
import json
import boto.ec2
from recordtype import recordtype

Network = recordtype('Network', [
    "net_name",
    "root_folder",
    "AWS_region",
    "AWS_ACCESS_KEY",
    "AWS_SECRET_KEY",
    "AWS_keypair",
    "AWS_security_group",
    "sync_node",
    "sync_node_user",
    "monitor_node",
    "bridge_node",
    "config_node",
    "mailgun_domain",
    "mailgun_key",
    "alert_recipients",
    "system_alert_recipients",
    "code_repo",
    "config_repo",
    "blobs_repo",
], default=None)

AMI_MAP = {
    "us-east-1": {
        "ubuntu": "ami-9eaa1cf6",
        "debian": "ami-9844f0f0"
    },
    "us-west-1": {
        "ubuntu": "ami-076e6542",
        "debian": "ami-5faca41a"
    },
    "us-west-2": {
        "ubuntu": "ami-3d50120d",
        "debian": "ami-d70341e7"
    },
    "eu-west-1": {
        "ubuntu": "ami-f0b11187",
        "debian": "ami-3051f047"
    },
}

def _(s): print(textwrap.dedent(s).strip())

def ask(msg, default): return raw_input("%s [%s]: " % (msg, default)) or default

def gen_key(path):
    subprocess.check_output(("ssh-keygen", "-t", "rsa" , "-N", "", "-b", "2048", "-f", path))

def make_security_group(name, conn):
    s = conn.create_security_group(name, 'Piloteur init Group')
    s.authorize('tcp', 80, 80, '0.0.0.0/0')
    s.authorize('tcp', 22, 22, '0.0.0.0/0')

def upload_key(path, name, conn):
    with open(path, 'r') as f:
        public_key_body = f.read()
    conn.import_key_pair(name, public_key_body)

def start_infra_node(name, conn, N):
    print
    instance_type = ask("Enter the instance type for the %s node" % name, "t2.micro")
    _("=> Creating a EC2 instance for the %s node" % name)
    instance = conn.run_instances(
        AMI_MAP[N.AWS_region]["ubuntu"],
        key_name=N.AWS_keypair,
        instance_type=instance_type,
        security_groups=[N.AWS_security_group],
    ).instances[0]
    _("=> Waiting for the %s node to start..." % name)
    while instance.state != 'running':
        time.sleep(5)
        instance.update()
    instance.add_tag('piloteur', name)
    return instance.ip_address

def init():
    _("""\
    Welcome. This procedure will guide you in making your first Piloteur network.
    Please note that you can't stop and resume this process.
    """)

    N = Network()

    print
    N.net_name = ask("Pick a name for your network", "")

    print
    N.root_folder = ask("Choose a folder to store your network configuration",
        "../%s-network" % N.net_name)
    N.root_folder = os.path.abspath(os.path.expanduser(N.root_folder))

    if os.path.exists(N.root_folder):
        _("The path already exists, aborting.")
        return

    print
    _("=> A config file will be placed at %s, use it to operate on your network"
        % os.path.join(N.root_folder, "cli-config.json"))

    os.makedirs(N.root_folder)
    os.makedirs(os.path.join(N.root_folder, "keys"))

    _("=> Generating keys and placing them in %s" % os.path.join(N.root_folder, "keys"))
    gen_key(os.path.join(N.root_folder, "keys", "%s-devices" % N.net_name))
    gen_key(os.path.join(N.root_folder, "keys", "%s-admin" % N.net_name))

    print
    _("""\
    Now you'll need to enter some information about your AWS account.
    You can generate a ACCESS_KEY at the following URL
    https://console.aws.amazon.com/iam/home?#security_credential
    """)

    print
    N.AWS_region = ask("AWS Region", "us-west-2")
    N.AWS_ACCESS_KEY = ask("AWS ACCESS_KEY", "")
    N.AWS_SECRET_KEY = ask("AWS SECRET_KEY", "")

    # print
    # _("""\
    # Now please go to the following URL, select Import Key Pair,
    # https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=%s#KeyPairs
    # and upload the following file,
    # %s
    # """ % (
    #     N.AWS_region,
    #     os.path.join(N.root_folder, "keys", "%s-admin.pub" % N.net_name)
    # ))
    # N.AWS_keypair = ask("AWS Keypair name", "%s-admin" % N.net_name)

    # print
    # _("""\
    # Now please go to the following URL, create a new Security Group,
    # https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=%s#SecurityGroups
    # with the following Inbound rules: SSH, HTTP
    # """ % N.AWS_region)
    # N.AWS_security_group = ask("AWS Security Group name", N.net_name)

    env = {
        'AWS_ACCESS_KEY_ID': N.AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': N.AWS_SECRET_KEY,
    }
    os.environ.update(env)
    conn = boto.ec2.connect_to_region(N.AWS_region)

    print
    N.AWS_security_group = "%s-%s" % (N.net_name, os.urandom(4).encode('hex'))
    _("=> Creating a Security group named %s" % N.AWS_security_group)
    make_security_group(N.AWS_security_group, conn)

    print
    N.AWS_keypair = "%s-admin-%s" % (N.net_name, os.urandom(4).encode('hex'))
    _("=> Creating a keypair named %s" % N.AWS_keypair)
    upload_key(os.path.join(N.root_folder, "keys", "%s-admin.pub" % N.net_name),
        N.AWS_keypair, conn)

    print
    sync_node = ask("[Advanced] If you already have a system you want to use as a sync node, enter the hostname/IP", "")
    if sync_node:
        _("""
        Please make sure that the admin key has access to the sync node.
        All the data will go to ~/piloteur
        """)
        N.sync_node = sync_node
        N.sync_node_user = ask("Enter the username for the sync node", "")
    else:
        instance_type = ask("Enter the instance type for the sync node", "m3.medium")
        size = ask("Enter the disk size in GB for the sync node", "50")
        _("=> Creating a EC2 instance for the sync node")
        dev_sda1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
        dev_sda1.size = int(size)
        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
        bdm['/dev/sda1'] = dev_sda1
        instance = conn.run_instances(
            AMI_MAP[N.AWS_region]["ubuntu"],
            key_name=N.AWS_keypair,
            instance_type=instance_type,
            security_groups=[N.AWS_security_group],
            block_device_map=bdm,
        ).instances[0]
        _("=> Waiting for the sync node to start...")
        while instance.state != 'running':
            time.sleep(5)
            instance.update()
        instance.add_tag('piloteur', 'sync')
        N.sync_node = instance.ip_address
        N.sync_node_user = 'ubuntu'

    N.monitor_node = start_infra_node("monitor", conn, N)
    N.bridge_node = start_infra_node("bridge", conn, N)
    N.config_node = start_infra_node("config", conn, N)

    print
    N.mailgun_domain = ask("Enter the Mailgun domain for alerts", "")
    N.mailgun_key = ask("Enter the Mailgun API key", "key-xxxxxxxxxx")
    _("Alerts will come from: Piloteur Alert Bot <alert@%s>" % N.mailgun_domain)

    print
    N.alert_recipients = [e.strip() for e in
        ask("Enter the comma separated list of email recipients for driver alerts", "").split(',')]
    N.system_alert_recipients = [e.strip() for e in
        ask("Enter the comma separated list of email recipients for system alerts", "").split(',')]

    print
    _("=> Creating a config repository")

    os.makedirs(os.path.join(N.root_folder, "piloteur-config"))
    os.makedirs(os.path.join(N.root_folder, "piloteur-config", "endpoint"))
    os.makedirs(os.path.join(N.root_folder, "piloteur-config", "monitor"))

    monitor_config = {
        "sync_nodes": [
            {"host": N.sync_node, "user": N.sync_node_user}
        ],
        "bridge_host": N.bridge_node,

        "loglevel": "INFO",

        "mailgun_domain": N.mailgun_domain,
        "mailgun_api_key": N.mailgun_key,
        "alert_mail_from": "Piloteur Alert Bot <alert@%s>" % N.mailgun_domain
    }
    with open(os.path.join(N.root_folder, "piloteur-config", "monitor", "config.json"), 'w') as f:
        json.dump(monitor_config, f, indent=4)

    monitor_config = {
        "sync_nodes": [
            {"host": N.sync_node, "user": N.sync_node_user}
        ],
        "ssh_bridge_host": N.bridge_node,

        "remote_chmod": "Du+rwx,Dg+rx,Dg-w,Fu+rw,Fu-x,Fg+r,Fg-wx,o-rwx",
        "data_path": "~/piloteur/data/",
        "logs_path": "~/piloteur/logs/",
        "logging_modules": [
            "monitor", "timesync", "watchdog", "versions", "pull", "classes", "iwconfig"
        ],
        "log_format": "[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s",
        "network_strikes_limit_mult": 100,
        "disable_network_reboot": False,

        "loaded_drivers": [],
        "driver_config": {},

        "alert_recipients": N.alert_recipients,
        "system_alert_recipients": N.system_alert_recipients
    }
    with open(os.path.join(N.root_folder, "piloteur-config", "endpoint", "config.json"), 'w') as f:
        json.dump(monitor_config, f, indent=4)

    wlan_cfg = textwrap.dedent("""\
        # This file gets copied to /etc/wpa_supplicant/wpa_supplicant.conf
        #
        # The basic case looks like this
        #
        # network={
        #     ssid="simple"
        #     psk="very secret passphrase"
        # }
        #
        # for more complex case see a really complete example here
        # http://hostap.epitest.fi/cgit/hostap/plain/wpa_supplicant/wpa_supplicant.conf
        #
        # <node-id>/wlan.<node-id>.cfg, if existing, replaces this file
    """)
    with open(os.path.join(N.root_folder, "piloteur-config", "endpoint", "wlan.cfg"), 'w') as f:
        f.write(wlan_cfg)

    subprocess.check_output(["git", "init"], cwd=os.path.join(N.root_folder, "piloteur-config"))
    subprocess.check_output(["git", "add", "-A"], cwd=os.path.join(N.root_folder, "piloteur-config"))
    subprocess.check_output(["git", "commit", "-m", "piloteur init"], cwd=os.path.join(N.root_folder, "piloteur-config"))

    print
    _("""
        A repository has been created at the following location
        %s
        Please push it to GitHub and make sure that ONLY the following key can access it
        %s
    """ % (
        os.path.join(N.root_folder, "piloteur-config"),
        os.path.join(N.root_folder, "keys", "%s-admin.pub" % N.net_name)
    ))
    N.config_repo = ask("Enter the ssh clone URL for the config repo",
        "git@github.com:xxx/piloteur-config.git")

    print
    _("""
    Make sure that the both the following keys have READ-ONLY access to the main and blobs repos
    %s
    %s
    """ % (
        os.path.join(N.root_folder, "keys", "%s-admin.pub" % N.net_name),
        os.path.join(N.root_folder, "keys", "%s-devices.pub" % N.net_name)
    ))
    N.code_repo = ask("Enter the ssh clone URL for the main piloteur repo",
        "git@github.com:piloteur/piloteur.git")
    N.blobs_repo = ask("Enter the ssh clone URL for the piloteur blobs repo",
        "git@github.com:piloteur/piloteur-blobs.git")

    print
    _("=> Writing the network config file")
    config = {
        "paths": {
            "virtualenv": os.path.join(N.root_folder, "ENV"),
            "keys": {
                "admin": os.path.join(N.root_folder, "keys", "%s-admin" % N.net_name),
                "devices": os.path.join(N.root_folder, "keys", "%s-devices" % N.net_name)
            },
            "config_repo": os.path.join(N.root_folder, "piloteur-config")
        },
        "nodes": {
            "bridge": N.bridge_node,
            "config": N.config_node,
            "sync": [
                {
                    "host": N.sync_node,
                    "user": N.sync_node_user
                }
            ],
            "monitor": N.monitor_node
        },
        "repositories": {
            "config_repo": N.config_repo,
            "config_rev": "master",
            "code_repo": N.code_repo,
            "code_rev": "master",
            "blobs_repo": N.blobs_repo,
            "blobs_rev": "master"
        },
        "AWS": {
            "region": N.AWS_region,
            "ACCESS_KEY": N.AWS_ACCESS_KEY,
            "SECRET_KEY": N.AWS_SECRET_KEY,
            "security_group": N.AWS_security_group,
            "keypair_name": N.AWS_keypair
        }
    }
    with open(os.path.join(N.root_folder, "cli-config.json"), 'w') as f:
        json.dump(config, f, indent=4)

    from .setup import setup, test

    print
    _("=> Setting up the environment")
    setup(config)

    from .ansible import deploy_special

    print
    _("=> Deploying the config node")
    deploy_special('config', config, env)
    print
    _("=> Deploying the bridge node")
    deploy_special('bridge', config, env)
    print
    _("=> Deploying the sync node")
    deploy_special('sync', config, env)
    print
    _("=> Deploying the monitor node")
    deploy_special('monitor', config, env)

    print
    _("=> Testing the environment")
    if test(config, env) != 0: return

    print
    _("""
    ## Success!
    From now on use the following argument with the piloteur command:
    --config=%s

    The monitor interface is at http://%s/
    """ % (os.path.join(N.root_folder, "cli-config.json"), N.monitor_node))
