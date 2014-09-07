#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Smarthome monitor.

Usage: monitor.py serve [--listen=<addr>]

Options:
  --listen ADDR  IP and port to bind to [default: 0.0.0.0:8080]
  -h --help      Show this screen.
  --version      Show version.

"""

import os.path
import json
import re
import paramiko
import time
import fnmatch
import arrow
import sqlite3
import sys
from docopt import docopt
from flask import Flask, Response
from flask import render_template, abort, url_for

import nexus
import nexus.private

PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT)
from monitor import get_tunnel_connections, fetch_data, assess_data


class Monitor():
    def __init__(self, config, db_path):
        self.config = config
        self.db_path = db_path
        self.last_connection = 0

    def nexus_init(self):
        # TODO: make this smarter
        if self.last_connection > time.time() - 60:
            return

        for _ in range(5):
            try:
                nexus.init(self.config)
            except paramiko.SSHException:
                continue
            self.last_connection = time.time()
            return

        abort(500)


    ### STATUS

    def serve_status(self, hub_id):
        if not re.match(r'^[a-z0-9-]+$', hub_id): abort(403)
        return render_template('status.html', hub_id=hub_id)

    def ajax_status(self, hub_id):
        if not re.match(r'^[a-z0-9-]+$', hub_id): abort(403)

        self.nexus_init()

        data = fetch_data(hub_id, self.config)
        result = assess_data(data, self.config)

        return render_template('ajax_status.html', h=result, nexus=nexus)


    ### SEARCH

    def serve_search(self, query):
        if not re.match(r'^[a-z0-9-\*\? ]+$', query): abort(403)
        return render_template('search.html', query=query)

    def ajax_search_refresh(self, query):
        return self.ajax_search(query, refresh=True)

    def ajax_search(self, query, refresh=False):
        if not re.match(r'^[a-z0-9-\*\? ]+$', query): abort(403)

        if refresh:
            self.nexus_init()
            all_hubs = nexus.list_hub_ids()
        else:
            c = sqlite3.connect(self.db_path).cursor()
            c.execute('SELECT hub_id FROM Cache')
            all_hubs = [row[0] for row in c.fetchall()]

        hubs = set()
        for keyword in query.split(' '):
            keyword = '*' + keyword.strip('*') + '*'
            hubs.update(fnmatch.filter(all_hubs, keyword))

        if len(hubs) == 1:
            return """
            <script>window.location.href = "{}";</script>
            """.format(url_for('serve_status', hub_id=list(hubs)[0]))

        results = []
        oldest_cache = arrow.utcnow()
        for hub_id in hubs:
            if refresh:
                data = fetch_data(hub_id, self.config)
                res = assess_data(data, self.config)

                results.append((
                    res.hub_id,
                    res.hub_health,
                    res.error or res.summary
                ))

                continue

            c.execute('SELECT * FROM Cache WHERE hub_id=?', [hub_id])
            for hub_id, hub_health, summary, cache_time in c.fetchall():
                cache_time = arrow.get(cache_time, 'YYYY-MM-DD HH:mm:ss')
                oldest_cache = min(cache_time, oldest_cache)

                hub_health = {
                    'RED': nexus.RED, 'YELLOW': nexus.YELLOW,
                    'GREEN': nexus.GREEN, 'FAIL': nexus.RED
                }[hub_health]

                results.append((hub_id, hub_health, summary))

        if refresh or not results: oldest_cache = None
        else: oldest_cache = oldest_cache.humanize()
        # else: oldest_cache = '{} ({})'.format(
        #     oldest_cache.humanize(),
        #     oldest_cache.format('YYYY-MM-DD HH:mm:ss ZZ')
        # )

        return render_template('ajax_search.html', results=results,
            nexus=nexus, oldest_cache=oldest_cache, query=query)


    ### INDEX

    def serve_index(self):
        return render_template('index.html')

    def ajax_index(self):
        c = sqlite3.connect(self.db_path).cursor()

        hubs_list = get_tunnel_connections(self.config['tunnel_info'])
        oldest_cache = arrow.utcnow()

        hubs = []
        for hub_id in sorted(hubs_list):
            c.execute('SELECT * FROM Cache WHERE hub_id=?', [hub_id])
            for hub_id, hub_health, summary, cache_time in c.fetchall():
                cache_time = arrow.get(cache_time, 'YYYY-MM-DD HH:mm:ss')
                oldest_cache = min(cache_time, oldest_cache)

                hub_health = {
                    'RED': nexus.RED, 'YELLOW': nexus.YELLOW,
                    'GREEN': nexus.GREEN, 'FAIL': nexus.RED
                }[hub_health]

                hubs.append((hub_id, hub_health, summary))

        return render_template('ajax_index.html', hubs=hubs,
            oldest_cache=oldest_cache, nexus=nexus)


    ### ALL

    def serve_all(self):
        return render_template('all.html')

    def ajax_all(self):
        self.nexus_init()

        hubs_list = get_tunnel_connections(self.config['tunnel_info'])

        results = []
        for hub_id in hubs_list:
            app.logger.info(hub_id)

            data = fetch_data(hub_id, self.config)
            res = assess_data(data, self.config)

            if res.error:
                color = nexus.RED
            elif res.hub_health != nexus.GREEN:
                color = nexus.YELLOW
            else:
                color = nexus.GREEN

            results.append((res.hub_id, color, res.error or res.summary))

        return render_template('ajax_search.html', results=results, nexus=nexus)


    ### SHOW

    def show_data(self, hub_id, driver_name):
        self.nexus_init()

        data = nexus.fetch_data(driver_name, hub_id=hub_id)
        if not data: abort(404)
        return Response(data, mimetype='text/plain')

    def show_logs(self, hub_id, driver_name):
        self.nexus_init()

        logs = nexus.fetch_logs(driver_name, hub_id=hub_id)
        if not logs: abort(404)
        return Response(logs, mimetype='text/plain')


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR, '..', 'config.json')) as f:
        config = json.load(f)

    M = Monitor(config, os.path.join(DIR, '..', 'cache.db'))

    arguments = docopt(__doc__, version='Smarthome monitor 0.4')

    app = Flask(__name__)

    app.add_url_rule("/", 'serve_index', M.serve_index)
    app.add_url_rule("/ajax/index/", 'ajax_index', M.ajax_index)

    # app.add_url_rule("/all", 'serve_all', M.serve_all)
    # app.add_url_rule("/ajax/all/", 'ajax_all', M.ajax_all)

    app.add_url_rule("/status/<hub_id>", 'serve_status', M.serve_status)
    app.add_url_rule("/ajax/status/<hub_id>", 'ajax_status', M.ajax_status)

    app.add_url_rule("/search/<query>", 'serve_search', M.serve_search)
    app.add_url_rule("/ajax/search/<query>", 'ajax_search', M.ajax_search)
    app.add_url_rule("/ajax/search/<query>/refresh",
        'ajax_search_refresh', M.ajax_search_refresh)

    app.add_url_rule("/show/<hub_id>/data/<driver_name>", 'show_data', M.show_data)
    app.add_url_rule("/show/<hub_id>/logs/<driver_name>", 'show_logs', M.show_logs)

    host, port = arguments['--listen'].split(':')
    # app.debug = True
    app.run(host, int(port))
