import flask
from flask.ext.cors import CORS, cross_origin
import hashlib
import os
import random
import requests
import time
import uuid
from werkzeug.contrib.cache import SimpleCache

app = flask.Flask(__name__)
cache = SimpleCache()
cors = CORS(app, resources={'/': {'origins': 'localhost'}})

CALLER_ID = os.environ.get('BOOLI_CALLER_ID')
API_KEY = os.environ.get('BOOLI_API_KEY')
BASE_URL = 'https://api.booli.se/sold?{query_string}&callerId={caller}&time={time}&unique={unique}&hash={hash}'


if CALLER_ID is None or API_KEY is None:
  raise AttributeError('The environment variables BOOLI_CALLER_ID and/or BOOLI_API_KEY cannot be empty.')


def booli_request(**query_string_dict):
    # Take the extras-dictionary and convert it into a query string
    query_string = "&".join(
        [key + '=' + str(value) for key, value in query_string_dict.items()]
    ) if query_string_dict else ''
    unique = str(uuid.uuid4()).replace('-', '')[:16]
    unix_timestamp = str(int(time.time()))
    sha = hashlib.sha1(str(CALLER_ID + unix_timestamp + API_KEY + unique).encode('utf-8')).hexdigest()
    url = BASE_URL.format(
        query_string=query_string,
        caller=CALLER_ID,
        time=unix_timestamp,
        unique=unique,
        hash=sha
    )
    return requests.get(url)


def get_total_count():
    req = booli_request(limit=1, q='stockholm')
    return req.json()['totalCount']


@app.route("/")
@cross_origin(origin='localhost')
def main():
    total_count = cache.get('total_count')
    if total_count is None:
        total_count = get_total_count()
        cache.set('total_count', total_count, timeout=60 * 60)
    offset = random.randrange(1, total_count - 1)
    req = booli_request(limit=1, offset=offset, q='stockholm')
    return flask.jsonify(**req.json()['sold'][0])


if __name__ == "__main__":
    app.run()
