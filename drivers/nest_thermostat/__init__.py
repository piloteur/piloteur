import time
import requests
import sys
import traceback
import datetime
import json
import multiprocessing.dummy

class NestThermostat():
    def __init__(self, devices, interval):
        self.devices = devices
        self.interval = interval

    def run(self):
        # for account in self.devices:
        #     self.login(account)

        start = time.time()
        while True:
            self.get()
            wait = self.interval - (time.time() - start) % self.interval
            time.sleep(wait)

    def login(self, account, stderr_lock):
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

            with stderr_lock:
                print >> sys.stderr, "%s logged in" % account['username']

            return True

        except Exception as e:
            error = traceback.format_exception_only(type(e), e)[-1].strip()
            with stderr_lock:
                print >> sys.stderr, "%s login failed: %s" % (
                    account['username'], error)

            return False

    def get(self):
        blob = {}
        blob["timestamp"] = datetime.datetime.utcnow().isoformat()
        blob["accounts"] = {}

        p = multiprocessing.dummy.Pool(len(self.devices))
        stderr_lock = multiprocessing.dummy.Lock()

        def f(account):
            if not 'access_token' in account:
                if not self.login(account, stderr_lock):
                    return

            try: r = self.query(account)
            except requests.exceptions.Timeout:
                with stderr_lock:
                    print >> sys.stderr, 'WARNING: timeout waiting for Nest API'
                return

            if not r.status_code == requests.codes.ok:
                self.login(account, stderr_lock)
                r = self.query(account)
            if not r.status_code == requests.codes.ok:
                with stderr_lock:
                    print >> sys.stderr, "%s query failed: %s" % (
                    account['username'], r.status_code)
                return

            data = r.json()

            if not 'device' in data:
                with stderr_lock:
                    print >> sys.stderr, 'ERROR: %s: malformed response from Nest: missing "device" key' % account['username']
                return

            for serial in account['serials']:
                if not serial in data['device']:
                    with stderr_lock:
                        print >> sys.stderr, 'ERROR: device %s not found in account %s' % (
                        serial, account['username'])

            blob["accounts"][account['username']] = data

        def f_wrapper(account):
            try: f(account)
            except:
                with stderr_lock:
                    print >> sys.stderr, 'ERROR: exception while processing account %s' % account['username']
                    traceback.print_exc()

        p.map(f, self.devices, 1)
        p.close()

        json.dump(blob, sys.stdout)
        sys.stdout.write('\n')

    def query(self, account):
        r = requests.get(account['transport_url'] + "/v2/mobile/user." + account['userid'],
                         headers={"User-Agent": "Nest/1.1.0.10 CFNetwork/548.0.4",
                                  "Authorization": "Basic " + account['access_token'],
                                  "X-nl-user-id": account['userid'],
                                  "X-nl-protocol-version": "1"},
                         timeout=10)
        return r
