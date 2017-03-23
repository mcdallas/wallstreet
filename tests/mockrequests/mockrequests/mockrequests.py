import re
import pickle
import os
import json
from unittest.mock import Mock

import requests

ABSPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def abspath(path):
    return os.path.join(ABSPATH, path)


def prepare_request(*args, **kwargs):
    r = requests.Request(*args, **kwargs)
    s = requests.Session()
    return s.prepare_request(r)


def are_equal(req1, req2):
    urls = req1.url == req2.url
    headers = req1.headers == req2.headers
    return all((urls, headers))


def side_effect(method, *args, **kwargs):
    """ Main function driving the Mock object """
    request = prepare_request(method, *args, **kwargs)

    d = load_map(method)
    for key, val in d.items():
        stored_url, stored_regex, stored_strict = val

        if request.url == stored_url or (stored_regex and re.compile(stored_regex).match(request.url)):
            saved_request = load_file(key, method)
            if not stored_strict:
                return saved_request
            else:
                if are_equal(request, saved_request):
                    return saved_request


def side_effect_get(*args, **kwargs):
    return side_effect('GET', *args, **kwargs)


def side_effect_post(*args, **kwargs):
    return side_effect('POST', *args, **kwargs)


def load_file(filename, method):
    """ Unpickles the response object """
    with open(abspath('response/%s/%s' % (method, filename)), 'rb') as fileobj:
        return pickle.load(fileobj)

get = Mock(side_effect=side_effect_get)
post = Mock(side_effect=side_effect_post)
Request = Mock(side_effect=side_effect)


class Session:
    get = get
    post = post

def dump(request):
    """ Pickles the given response object to a folder corresponding to the request method """
    method = request.request.method

    i = 1
    while os.path.exists(abspath('response/%s/response%s.p' % (method, i))):
        i += 1
    filename = 'response%s.p' % i
    with open(abspath('response/%s/%s' % (method, filename)), 'wb') as fileobj:
        pickle.dump(request, fileobj)
    return filename


def load_map(method):
    """ Loads the map file from disk """
    try:
        with open(abspath('response/%s/map.json' % method), 'r') as fileobj:
            d = json.load(fileobj)
    except FileNotFoundError:
        d = {}
    return d


def save_map(d, method):
    """ Saves the map file to disk """
    if not d:
        d = {}
    with open(abspath('response/%s/map.json' % method), 'w') as fileobj:
        json.dump(d, fileobj)


def save(response, regex=None, strict=False):
    """ Saves the response object and creates a reference to it in the map file """
    request = response.history[0].request if response.history else response.request  # The original request object
    url = request.url
    method = response.request.method

    filename = dump(response)

    d = load_map(method)
    d[filename] = [url, regex, strict]
    save_map(d, method)
