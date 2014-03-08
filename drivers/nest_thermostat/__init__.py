import time
import requests
import sys
import traceback
import datetime
import json

class NestThermostat():
    def __init__(self, devices, interval):
        self.devices = devices
        self.interval = interval

    def run(self):
        self.login()

        start = time.time()
        while True:
            self.get()
            wait = self.interval - (time.time() - start) % self.interval
            time.sleep(wait)

    def login(self):
        for account in self.devices:
            try:
                r = requests.post("https://home.nest.com/user/login",
                                  data = {"username": account['username'],
                                          "password": account['password']},
                                  headers = {"User-Agent":
                                  "Nest/1.1.0.10 CFNetwork/548.0.4"})
                r.raise_for_status()

                data = r.json()

                account['transport_url'] = data["urls"]["transport_url"]
                account['access_token'] = data["access_token"]
                account['userid'] = data["userid"]

                print >> sys.stderr, "%s logged in" % account['username']

            except Exception as e:
                error = traceback.format_exception_only(type(e), e)[-1].strip()
                print >> sys.stderr, "%s login failed: %s" % (
                    account['username'], error)

    def get(self):
        blob = {}
        blob["timestamp"] = datetime.datetime.now().isoformat()
        blob["accounts"] = {}

        for account in self.devices:
            r = self.query(account)
            if not r.status_code == requests.codes.ok:
                self.login()
                r = self.query(account)
            if not r.status_code == requests.codes.ok:
                print >> sys.stderr, "%s query failed: %s" % (
                    account['username'], r.status_code)
                continue

            data = r.json()

            for serial in account['serials']:
                if not serial in data['device']:
                    print >> sys.stderr, 'ERROR: device %s not found in account %s' % (
                        serial, account['username'])

            blob["accounts"][account['username']] = data

        json.dump(blob, sys.stdout)
        sys.stdout.write('\n')

    def query(self, account):
        r = requests.get(account['transport_url'] + "/v2/mobile/user." + account['userid'],
                         headers={"User-Agent": "Nest/1.1.0.10 CFNetwork/548.0.4",
                                  "Authorization": "Basic " + account['access_token'],
                                  "X-nl-user-id": account['userid'],
                                  "X-nl-protocol-version": "1"})
        return r
