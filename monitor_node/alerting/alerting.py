#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os.path
import json
import time
import sqlite3
import logging
import paramiko
import arrow
import requests
import jinja2

import nexus
import nexus.private
import nexus.monitor


PERIOD = 10


class Alerting():
    def __init__(self, config, db, log, tmpl_dir):
        self.config = config
        self.log = log
        self.db = db
        self.last_time = 0
        self.tmpl_env = jinja2.Environment(loader=jinja2.FileSystemLoader(tmpl_dir))

    def _send_mail(self, data):
        subject = self.tmpl_env.get_template('subject.jinja2').render(**data).strip()
        body = self.tmpl_env.get_template('body.jinja2').render(**data)

        to = data['config']['alert_recipients']
        if data['hub_health'] == 'FAIL': to += data['config']['system_alert_recipients']

        self.log.debug("Sending a mail to {}".format(to))

        return requests.post(
            "https://api.mailgun.net/v2/{}/messages".format(self.config['mailgun_domain']),
            auth=("api", self.config['mailgun_api_key']),
            data={"from": self.config['alert_mail_from'],
                  "to": to,
                  "subject": subject,
                  "text": body})

    def start(self):
        self.log.debug('Starting...')

        while True:
            self.last_time = time.time()

            self.run()

            # c = self.db.cursor()
            # c.execute("""INSERT OR REPLACE INTO Info (name, value)
            #     VALUES ('cache_age', ?);""", time.time())
            # self.db.commit()

            if self.last_time + PERIOD > time.time():
                time.sleep(self.last_time + PERIOD - time.time())

    def run(self):
        for _ in range(5):
            try:
                nexus.init(self.config)
            except paramiko.SSHException:
                continue
            break
        else:
            logging.error('Could not log in')
            exit(1)

        self.log.debug('Logged in.')

        all_hubs = nexus.list_hub_ids()
        for hub_id in all_hubs:
            data = nexus.monitor.fetch_data(hub_id)
            res = nexus.monitor.assess_data(data)

            hub_health = {
                nexus.RED: 'RED', nexus.YELLOW: 'YELLOW', nexus.GREEN: 'GREEN'
            }[res.hub_health]

            if res.error: hub_health = 'FAIL'

            c = self.db.cursor()
            c.execute('SELECT * FROM Cache WHERE hub_id=?', [res.hub_id])
            for _, old_health, old_summary, old_time in c.fetchall():
                if old_health == hub_health: break

                a = arrow.get(old_time, 'YYYY-MM-DD HH:mm:ss')

                info = {
                    'hub_id': res.hub_id,
                    'hub_health': hub_health,
                    'summary': res.error or res.summary,
                    'time': arrow.utcnow().format('YYYY-MM-DD HH:mm:ss ZZ'),
                    'human_old_time': a.humanize(),
                    'old_time': a.format('YYYY-MM-DD HH:mm:ss ZZ'),
                    'old_health': old_health,
                    'old_summary': old_summary,
                    'config': data.config,
                }

                if hub_health == 'FAIL':
                    self.log.info("{hub_id} failed: {summary} "
                        "[was: {old_health} - {old_time}]".format(**info))

                    self._send_mail(info)
                    break

                # If the status went to GREEN or got worse (* -> R || G -> Y)
                if hub_health == 'GREEN' or hub_health == 'RED' or (
                    old_health == 'GREEN' and hub_health == 'YELLOW'):
                    self.log.info("{hub_id} is {hub_health}: {summary} "
                        "[was: {old_health} - {old_time}]".format(**info))

                    self._send_mail(info)

            self.log.debug("{} is {}: {}".format(
                res.hub_id,
                hub_health,
                res.error or res.summary
            ))

            c.execute("""INSERT OR REPLACE INTO Cache
                (hub_id, hub_health, summary, time)
                VALUES (?, ?, ?, datetime('now'));""", (
                    res.hub_id,
                    hub_health,
                    res.error or res.summary
            ))
            self.db.commit()


if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(name)s: %(message)s")
    logging.Formatter.converter = time.gmtime
    log = logging.getLogger('ALERTING')
    log.setLevel(logging.INFO)

    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, '..', 'config.json')) as f:
        config = json.load(f)

    conn = sqlite3.connect(os.path.join(DIR, '..', 'cache.db'))

    c = conn.cursor()
    # c.execute("""CREATE TABLE IF NOT EXISTS Info
    #     (name TEXT PRIMARY KEY, value TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS Cache
        (hub_id TEXT PRIMARY KEY, hub_health TEXT,
        summary TEXT, time TIMESTAMP)""")
    conn.commit()

    A = Alerting(config, conn, log, DIR)
    A.start()
