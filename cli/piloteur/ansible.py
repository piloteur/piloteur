#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import absolute_import

import os
import boto.ec2
import time
import logging

from .util import call_ansible, AMI_MAP

def start_ec2_node(os, instance_type, node_type, name, conn, config):
    logging.info("Starting a EC2 instance...")
    instance = conn.run_instances(
        AMI_MAP[config["AWS"]["region"]][os],
        key_name=config["AWS"]["keypair_name"],
        instance_type=instance_type,
        security_groups=[config["AWS"]["security_group"]],
    ).instances[0]
    logging.info("Waiting for it to boot...")
    while instance.state != 'running':
        time.sleep(5)
        instance.update()
    instance.add_tag('piloteur', node_type)
    if name: instance.add_tag('Name', name)
    return instance.ip_address

def setup_rpi(host):
    pass

def create_endpoint(on, at, node_id, node_classes, aws_type, config, env):
    if on == "ec2":
        os.environ.update(env)
        conn = boto.ec2.connect_to_region(config["AWS"]["region"])
        user = "admin"
        host = start_ec2_node("debian", aws_type, "endpoint", node_id, conn, config)
    elif on == "rpi":
        setup_rpi(host)
        user, host = 'pi', at

    call_ansible([
        "-i", "%s," % host,
        "-e", "initial_user=%s node_id=%s node_classes=%s config_node_addr=%s" %
        (user, node_id, node_classes, "http://%s" % config["nodes"]["config"]),
        "endpoint_node.yml"
    ], config, env)

    print "Successfully created a new endpoint (%s): %s" % (node_id, host)

def create_infra(node_type, on, at, aws_type, config, env):
    if on == "ec2":
        os.environ.update(env)
        conn = boto.ec2.connect_to_region(config["AWS"]["region"])
        user = "ubuntu"
        host = start_ec2_node("ubuntu", aws_type, node_type, None, conn, config)
    elif on == "arbitrary":
        user, host = at.split('@')

    call_ansible([
        "-i", "%s," % host,
        "-e", "initial_user=%s" % user,
        "%s_node.yml" % node_type
    ], config, env)

    print "Successfully created a %s: %s" % (node_type, host)
