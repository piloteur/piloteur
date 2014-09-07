import subprocess
import sys
import json

config = json.loads(sys.stdin.read())

print >> sys.stderr, 'Starting Open-Zwave binary...'

subprocess.check_call(['sudo', '/usr/local/bin/MinOZW'])
