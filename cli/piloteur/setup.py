#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import os.path
import yaml
import textwrap
import requests
import logging
import subprocess
import os
import nexus

from .util import init_nexus, dep_call, open_ssh, CODE, DEPLOYMENT

def setup(config):
    ### repo_definitions.yml
    logging.info("Creating the repo_definitions.yml file...")
    definitions_path = os.path.join(DEPLOYMENT, 'repo_definitions.yml')
    with open(definitions_path, 'w') as f:
        print >> f, "# WARNING: autogenerated file\n"
        yaml.dump(config['repositories'], f)

    ### inventory.ini
    logging.info("Creating the inventory.ini file...")
    inventory = textwrap.dedent("""
    [local]
    localhost ansible_connection=local

    [bridge-nodes]
    {config[nodes][bridge]}

    [monitor-nodes]
    {config[nodes][monitor]}

    [config-nodes]
    {config[nodes][config]}

    [raspberrypi]
    {config[addresses][rpi]}

    [sync-nodes]
    """).strip().format(config=config)
    for sync_node in config['nodes']['sync']:
        inventory += "\n{host} ansible_ssh_user={user}".format(**sync_node)
    inventory_path = os.path.join(DEPLOYMENT, 'inventory.ini')
    with open(inventory_path, 'w') as f:
        print >> f, "# WARNING: autogenerated file\n"
        print >> f, inventory

    ### ec2.ini
    logging.info("Creating the ec2.ini file...")
    ec2 = textwrap.dedent("""
    [ec2]
    regions = {config[AWS][region]}
    regions_exclude = us-gov-west-1,cn-north-1
    destination_variable = public_dns_name
    vpc_destination_variable = ip_address
    route53 = False
    all_instances = False
    all_rds_instances = False
    cache_path = ~/.ansible/tmp
    cache_max_age = 300
    nested_groups = False
    """).strip().format(config=config)
    ec2_ini_path = os.path.join(DEPLOYMENT, 'ec2.ini')
    with open(ec2_ini_path, 'w') as f:
        print >> f, "# WARNING: autogenerated file\n"
        print >> f, ec2

    ### ec2.py
    ec2_py_path = os.path.join(DEPLOYMENT, 'ec2.py')
    if not os.path.exists(ec2_py_path):
        logging.info("Downloading the ec2.py file...")
        r = requests.get("https://raw.githubusercontent.com/ansible/ansible/1dc11c97525e1a387b1eacb50a1ad45fe6297d7b/plugins/inventory/ec2.py")
        with open(ec2_py_path, 'w') as f:
            f.write(r.text)
        os.chmod(ec2_py_path, 0755)
    else:
        logging.info("ec2.py present, skipping")

    ### virtualenv
    if not os.path.exists(config["paths"]["virtualenv"]):
        logging.info("Creating the virtualenv...")
        subprocess.check_call(
            ["virtualenv", "-p", "python2.7", config["paths"]["virtualenv"]])
        pip_path = os.path.join(config["paths"]["virtualenv"], "bin", "pip")
        subprocess.check_call(
            [pip_path, "install", "ansible==1.5.3", "boto==2.32.1"])
    else:
        logging.info("virtualenv exists, skipping")

def test(config, env):
    ### ec2.py
    logging.info("Testing ec2.py...")
    try:
        dep_call(["./ec2.py", "--list"], config, env)
    except subprocess.CalledProcessError:
        logging.error("ERROR: Error executing ec2.py, check your AWS credentials")
        return 1

    # TODO: test the keypair and the security group

    ### ssh keys
    logging.info("Testing SSH keys...")
    for name in ("piloteur-admin", "piloteur-devices",
                 "piloteur-admin.pub", "piloteur-devices.pub"):
        if not os.path.exists(os.path.join(CODE, "keys", name)):
            logging.error("The key %s is missing, place it in the keys/ folder", name)
            return 1
    try: open_ssh("github", config).close()
    except:
        logging.error("ERROR: Failed to authenticate with GitHub")
        return 1

    ### nodes
    logging.info("Testing infrastructure nodes...")
    for node_name in ("monitor", "bridge", "config"):
        try: open_ssh(node_name, config).close()
        except:
            logging.error("ERROR: Failed to log into %s", node_name)
            return 1

    ### nexus
    logging.info("Testing nexus login to ...")
    try:
        init_nexus(config)
        nexus.list_node_ids()
    except:
        logging.error("ERROR: Failed to make nexus work, probably sync node unreachable")
        return 1

    return 0
