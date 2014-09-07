import time
import sys
import json
import Crypto

config = json.loads(sys.stdin.read())
print config

while True:
  print >> sys.stderr, 'Hello world!'
  time.sleep(10)
