import os
import sys
import time
import signal
import base64
import hashlib
import logging
import asyncio
import requests
import argparse
import functools

import prettytable

from tqdm import tqdm
from requests_toolbelt import MultipartEncoder

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ._version import __version__

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


class InvalidToken(Exception):
    pass


class PathError(Exception):
    pass


class MD5Error(Exception):
    pass


class TimeoutException(Exception):
    pass


class AuthorizationError(Exception):
    pass


class Utils(object):
    def __init__(self, access_token):
        self.access_token = access_token
        self.pcsserver = get_fastest_pcs_server()
        self.pcsurl = "https://{server}/rest/2.0/pcs/".format(
            server=self.pcsserver)

    def _remove_empty_items(self, data):
        for k, v in data.items():
            if not v:
                data.pop(k)

    def _request(self, uri, method, url=None, extra_params=None,
                 data=None, files=None, outfile=None, **kwargs):
        params = {
            'method': method,
            'access_token': self.access_token
        }
        if extra_params:
            params.update(extra_params)
            self._remove_empty_items(params)

        if not url:
            url = self.pcsurl + uri
        api = url
        if data or files:
            api = '%s?%s' % (url, urlencode(params))
            if data:
                self._remove_empty_items(data)
            else:
                self._remove_empty_items(files)
                data = MultipartEncoder(files)
                if kwargs.get('headers'):
                    kwargs['headers']['Content-Type'] = data.content_type
                else:
                    kwargs['headers'] = {'Content-Type': data.content_type}
            response = requests.post(api, data=data, **kwargs)
        else:
            if outfile:
                downchunks(api, params, outfile)
                return
            else:
                response = requests.get(api, params=params, **kwargs)
        return response


def check_token(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.status_code == 401:
            raise InvalidToken('Access token invalid or no longer valid')
        else:
            return response
    return wrapper


raw_input = input


def human_size(num):
    for unit in ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s" % (num, unit)
        num /= 1024.0
    return "%.1f%s" % (num, 'Y')


def ask_input(msg, enter=True):
    print(msg)
    if enter:
        print('Press [Enter] when you are done')
    return raw_input()


def loger(logfile=None, level="info"):
    logger = logging.getLogger()
    if level.lower() == "info":
        logger.setLevel(logging.INFO)
        f = logging.Formatter(
            '[%(levelname)s %(asctime)s] %(message)s')
    elif level.lower() == "debug":
        logger.setLevel(logging.DEBUG)
        f = logging.Formatter(
            '[%(levelname)s %(threadName)s %(asctime)s %(funcName)s(%(lineno)d)] %(message)s')
    if logfile is None:
        h = logging.StreamHandler(sys.stdout)
    else:
        h = logging.FileHandler(logfile, mode='w')
    h.setFormatter(f)
    logger.addHandler(h)
    return logger


class Chunk(object):
    OneK = 1024
    OneM = OneK * OneK
    OneG = OneM * OneK
    OneT = OneG * OneK
    OneP = OneT * OneK
    OneE = OneP * OneK
    OneZ = OneE * OneK
    OneY = OneZ * OneK


STYLE = {
    "default": {
        "end": 0
    },
    "back": {
        "blue": 44,
        "black": 40,
        "yellow": 43,
        "cyan": 46,
        "purple": 45,
        "green": 42,
        "white": 47,
        "red": 41
    },
    "fore": {
        "blue": 34,
        "black": 30,
        "yellow": 33,
        "cyan": 36,
        "purple": 35,
        "green": 32,
        "white": 37,
        "red": 31
    },
    "mode": {
        "mormal": 0,
        "hide": 8,
        "bold": 1,
        "invert": 7,
        "blink": 5,
        "underline": 4
    }
}


def style(string, mode='', fore='', back=''):
    mode = '%s' % STYLE["mode"].get(mode, "")
    fore = '%s' % STYLE['fore'].get(fore, "")
    back = '%s' % STYLE['back'].get(back, "")
    style = ';'.join([s for s in [mode, fore, back] if s])
    return "\033[%sm%s\033[0m" % (style, string)


def getfilemd5(filename):
    if not os.path.isfile(filename):
        return
    myHash = hashlib.md5()
    f = open(filename, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myHash.update(b)
    f.close()
    return myHash.hexdigest()


def downchunks(api, params, outfile):
    filename = outfile["path"]
    filesize = outfile["size"]
    filemd5 = outfile["md5"]
    _chunk_size = 1 * Chunk.OneM  # 1 M
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    offset = 0
    headers = {}
    if os.path.isfile(filename):
        offset = os.path.getsize(filename)
        if offset == filesize:
            return
        headers = {"Range": "bytes={}-".format(offset)}
    md5 = hashlib.md5()
    with tqdm(total=int(filesize), initial=offset, unit='', ascii=True, unit_scale=True) as bar:
        bar.set_description(filename)
        with requests.get(api, params=params, headers=headers, stream=True) as res:
            with open(filename, offset and "ab" or "wb") as fo:
                for chunk in res.iter_content(chunk_size=_chunk_size):
                    if chunk:
                        fo.write(chunk)
                        fo.flush()
                        md5.update(chunk)
                        bar.update(_chunk_size)
    if filemd5 != md5.hexdigest():
        raise MD5Error("MD5 check Error %s" % filename)


def get_fastest_pcs_server_test():
    ret = requests.get(
        'https://pcs.baidu.com/rest/2.0/pcs/manage?method=listhost')
    serverlist = [server['host'] for server in ret.json()['list']]
    url_pattern = 'http://{0}/monitor.jpg'
    time_record = []
    for server in serverlist:
        start = time.time() * 1000
        url = url_pattern.format(server)
        try:
            requests.get(url, timeout=10)
        except:
            continue
        end = time.time() * 1000
        time_record.append((end - start, server))
    if len(time_record):
        return min(time_record)[1]  # bj.baidupcs.com
    return ""


def get_fastest_pcs_server():
    url = 'http://pcs.baidu.com/rest/2.0/pcs/file?method=locateupload'
    ret = requests.get(url).json()
    return ret['host']


def parseArg():
    subargs = ["login", "download", "info", "logout", "list", "ls"]
    main_parser = argparse.ArgumentParser(
        description="baidu netdisk command-line utils.",)
    mode_parser = main_parser.add_argument_group("Commands options")
    mode_parser.add_argument("mode",  metavar="{%s}" % ",".join(
        subargs), help="command to run.", choices=subargs)
    args = main_parser.parse_args(sys.argv[1:2])
    mode = args.mode
    if mode == "login":
        des = "login baidu user count."
    if mode == "logout":
        des = "logout baidu user count."
    elif mode == "info":
        des = "show logined baidu netdisk information and exit."
    elif mode in ["list", "ls"]:
        des = "list remote netdisk file or directory."
    elif mode == "download":
        des = "download file or directory from netdisk to local directory."
    parser = argparse.ArgumentParser(
        description=des, prog=" ".join(sys.argv[0:2]))
    general_parser = parser.add_argument_group("General options")
    general_parser.add_argument("mode", metavar=mode, choices=subargs)
    general_parser.add_argument('-v', '--version',
                                action='version', version="v" + __version__)
    if mode == "login":
        parser_login = parser.add_argument_group("Options")
    if mode == "logout":
        parser_logout = parser.add_argument_group("Options")
    elif mode == "info":
        parser_info = parser.add_argument_group("Options")
    elif mode in ["list", "ls"]:
        parser_list = parser.add_argument_group("Options")
        parser_list.add_argument(
            "path", type=str, help="remote path", default="/", nargs="?", metavar="<path>")
    elif mode == "download":
        parser_download = parser.add_argument_group("Options")
        parser_download.add_argument("-i", "--input", type=str, help="input file or directory of remote path to download, required",
                                     required=True, metavar="<file/dir>")
        parser_download.add_argument("-o", "--outdir", type=str, help="local directory for download, it will be create if not exists. required",
                                     required=True, metavar="<dir>")
        parser_download.add_argument('-t', "--threads", help="which number of file for download in parallel, default 1",
                                     type=int, default=1, metavar="<int>")
    return parser.parse_args()


def category_decode(code=6):
    code = str(code)
    co_map = {
        "1": "视频",
        "2": "音频",
        "3": "图片",
        "4": "文档",
        "5": "应用",
        "6": "其他",
        "7": "种子",
    }
    c = []
    cs = code.split(",")
    for i in cs:
        c.append(co_map.get(i.strip(), "其他"))
    return ",".join(c)


def confirm(message="Proceed", choices=("yes", "no"), default="yes"):
    assert default in choices, default
    options = []
    for option in choices:
        if option == default:
            options.append('[%s]' % option[0])
        else:
            options.append(option[0])
    message = "%s (%s)? " % (message, '/'.join(options))
    choices = {alt: choice
               for choice in choices
               for alt in [choice, choice[0]]}
    choices[''] = default
    while True:
        sys.stdout.write(message)
        sys.stdout.flush()
        user_choice = sys.stdin.readline().strip().lower()
        if user_choice not in choices:
            print("Invalid choice: %s" % user_choice)
        else:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return choices[user_choice]


def interrupt(signum, frame):
    raise TimeoutException()


def _timeout(timeout_secs, func, *args, **kwargs):
    default_return = kwargs.pop('default_return', "")

    signal.signal(signal.SIGALRM, interrupt)
    signal.alarm(timeout_secs)

    try:
        ret = func(*args, **kwargs)
        signal.alarm(0)
        return ret
    except (TimeoutException,  KeyboardInterrupt):
        return default_return


def ask(msg="", timeout=100):
    sys.stdout.write(msg)
    content = _timeout(timeout, sys.stdin.readline)
    if not content:
        sys.stdout.write("\n")
    return content.strip()
