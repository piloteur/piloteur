import time
import sys
import json
import os

config = json.loads(sys.stdin.read())

print >> sys.stderr, 'This goes to the logs.'
print >> sys.stderr, os.getcwd()
print >> sys.stderr, config

print 'This goes to data.'

while True:
    print >> sys.stderr, "It's %d" % time.time()
    print "I'm alive!" # The standard check makes sure data was logged recently
    time.sleep(10)
