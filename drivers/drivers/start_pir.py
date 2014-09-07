
import subprocess
import sys
import json

config = json.loads(sys.stdin.read())

print >> sys.stderr, 'Starting pir  binary...'

subprocess.check_call(['sudo', '/usr/local/bin/pir_interrupts.py'])

