#!/usr/bin/env python
# coding: utf-8

import os
import sys
import pdb
import json
import requests

from .utils import *


class Authorization(object):

    if os.getenv("BAIDU_API_KEY", ""):
        app_key = os.getenv("BAIDU_API_KEY")
    else:
        app_key = base64.b64decode(
            "NnFHdWRiOU5Jb1pOVlVtazNHOENBdHlMV01xcXh5R1k=".encode()).decode()

    if os.getenv("BAIDU_API_SECRET", ""):
        sec_key = os.getenv("BAIDU_API_SECRET")
    else:
        sec_key = base64.b64decode(
            "bm5HdTFXUE1NVDAwR3VBdURhMjlUZFJsMXNMczdpalU=".encode()).decode()

    code_url = "http://openapi.baidu.com/oauth/2.0/authorize"
    code_par = {
        "response_type": "code",
        "client_id": app_key,
        "redirect_uri": "oob",
        "scope": "basic netdisk"
    }

    token_url = refresh_url = "https://openapi.baidu.com/oauth/2.0/token"
    token_par = {
        "grant_type": "authorization_code",
        "code": "",
        "client_id": app_key,
        "client_secret": sec_key,
        "redirect_uri": "oob",
    }
    refresh_par = {
        "grant_type": "refresh_token",
        "refresh_token": "",
        "client_id": app_key,
        "client_secret": sec_key,
    }

    def __init__(self, AppKey="", SecretKey=""):
        self.client_id = AppKey or self.app_key
        self.client_secret = SecretKey or self.sec_key
        self.token = None
        self.token_file = os.path.expanduser("~/.bpan.json")
        if os.path.isfile(self.token_file):
            self.load_token()

    def get_code(self):
        self.code_par["client_id"] = self.client_id
        url = '%s?%s' % (self.code_url, urlencode(self.code_par))
        url = style(url, fore="blue")
        msg = 'Please visit:\n%s\nfor Login and' % url + \
            '\nPaste the Authorization Code here within 10 minutes.\n'
        msg += "Authorization Code (Press [Enter] when you are done): "
        self.auth_code = ask(msg, timeout=10*60).strip()
        return self.auth_code

    def get_token(self):
        self.token_par["code"] = self.auth_code
        self.token_par["client_id"] = self.client_id
        self.token_par["client_secret"] = self.client_secret
        url = '%s?%s' % (self.token_url, urlencode(self.token_par))
        res = requests.get(url)
        if res.status_code == 200:
            self.token = res.json()
            self.store_token()
        else:
            raise AuthorizationError()

    def refresh_token(self, refresh_token=""):
        if not refresh_token:
            if os.path.isfile(self.token_file):
                self.load_token()
                refresh_token = self.token["refresh_token"]
            else:
                raise InvalidToken("No refresh_token.")
        self.refresh_par["refresh_token"] = refresh_token
        self.refresh_par["client_id"] = self.client_id
        self.refresh_par["client_secret"] = self.client_secret
        url = '%s?%s' % (self.refresh_url, urlencode(self.refresh_par))
        res = requests.get(url)
        if res.status_code == 200:
            self.token = res.json()
            self.store_token()
        else:
            raise AuthorizationError()

    def store_token(self, filepath=""):
        if not filepath:
            filepath = self.token_file
        if self.token:
            with open(filepath, "w") as fo:
                json.dump(self.token, fo, indent=2)

    def load_token(self, filepath=""):
        if not filepath:
            filepath = self.token_file
        with open(filepath) as fi:
            self.token = json.load(fi)

    def login(self, force=False):
        if force or not self.token:
            code = self.get_code()
            if not code:
                self.loger.error("No authorization code input, login error.")
                sys.exit(1)
            try:
                self.get_token()
            except:
                self.loger.error("Invaliad code, login error.")
                sys.exit(1)

    def logout(self):
        time.sleep(3)
        if os.path.isfile(self.token_file):
            os.remove(self.token_file)
        self.token = None

    @property
    def loger(self):
        return logging.getLogger()

    def isLogin(self, msg=""):
        if not os.path.isfile(self.token_file):
            if msg:
                self.loger.error(msg)
                sys.exit(1)
            return False
        return True


class Bpan(Utils):

    BASE_APP_PATH = "/apps/Bpan/"

    def info(self, **kwargs):
        quota = self._request('quota', 'info', **kwargs).json()
        uinfo = self._request("", url="https://{server}/rest/2.0/xpan/nas".format(
            server="pan.baidu.com"), method="uinfo").json()
        total = human_size(quota["quota"])
        used = human_size(quota["used"])
        username = uinfo["baidu_name"]
        vip = uinfo["vip_type"]
        print("username: %s\nvip_type: %s\ntotal_size: %s\nused: %s" %
              (username, vip, total, used))

    async def _download_file(self, remotepath=None, outpath=None, flist=None, **kwargs):
        async with self.sem:
            if not remotepath:
                remotepath = self.remotepath
            else:
                remotepath = self._format_path(remotepath)
            self.loger.debug("star download %s file", remotepath)
            params = {'path': os.path.join(self.BASE_APP_PATH, remotepath), }
            url = self.pcsurl + "file"
            outfile = {}
            outfile["path"] = outpath
            if flist:
                outfile["size"] = flist["size"]
                outfile["md5"] = flist["md5"]
            else:
                s, m = self.get_file_size(remotepath)
                outfile["size"] = s
                outfile["md5"] = m
            res = await self.loop.run_in_executor(None, functools.partial(self._request, 'file', 'download', url=url, extra_params=params, outfile=outfile, **kwargs))
            self.loger.debug("finish download %s file", remotepath)

    def _format_path(self, remotepath):
        if not remotepath.startswith(self.BASE_APP_PATH):
            return remotepath.lstrip("/")
        else:
            return remotepath[len(self.BASE_APP_PATH):]

    def _walk_remote_dir(self, remotepath="", recursive=True):
        remote_list = self.remote_path_info(
            remotepath, bind=False).json()["list"]
        ds = [p for p in remote_list if p["isdir"]]
        fs = [p for p in remote_list if not p["isdir"]]
        for f in fs:
            yield f
        if not recursive:
            for d in ds:
                yield d
            return
        if not len(ds):
            return
        else:
            for d in ds:
                for f in self._walk_remote_dir(d["path"]):
                    yield f

    def get_file_mata(self, remotepath=""):
        if not remotepath:
            remotepath = self.remotepath
        else:
            remotepath = self._format_path(remotepath)
        params = {
            'path': os.path.join(self.BASE_APP_PATH, remotepath), }
        meta = self._request('file', 'meta',
                             extra_params=params).json()['list'][0]
        return meta

    def get_file_size(self, remotepath=""):
        info = self.get_file_mata(remotepath)
        return info["size"], info["md5"]

    @property
    def isfile(self):
        return not self.isdir

    @property
    def isdir(self):
        return self._path_info["isdir"] and True or False

    def remote_path_info(self, remotepath="", bind=True):
        remotepath = self._format_path(remotepath)
        params = {
            'path': os.path.join(self.BASE_APP_PATH, remotepath),
            'by': 'name',
            'order': 'asc'}
        res = self._request('file', 'list',
                            extra_params=params)
        if res.status_code != 200:
            raise PathError("path not exists %s" % remotepath)
        if bind:
            self.remotepath = remotepath
            self._path_info = self.get_file_mata()
            return
        return res

    async def _download_dir(self, outdir, nt=5):
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        tasks = []
        for f in self._walk_remote_dir(self.remotepath):
            rpath = f["path"]
            prefix = rpath[len(self.BASE_APP_PATH):].lstrip("/")
            if prefix.find("/") >= 0:
                outpath = os.path.join(
                    outdir, prefix[prefix.index("/"):].lstrip("/"))
            else:
                outpath = os.path.join(outdir, prefix)
            tasks.append(self._download_file(
                remotepath=rpath, outpath=outpath, flist=f))
        await asyncio.wait(tasks)

    @property
    def loger(self):
        return logging.getLogger()

    def download(self, outdir, nt=5):
        self.sem = asyncio.Semaphore(nt)
        self.loop = asyncio.get_event_loop()
        if self.isfile:
            self.loop.run_until_complete(self._download_file(outpath=os.path.join(
                outdir, os.path.basename(self.remotepath))))
        elif self.isdir:
            self.loop.run_until_complete(self._download_dir(outdir, nt))
        self.loop.close()

    def list(self):
        l = []
        meta = self._path_info
        if self.isfile:
            size = human_size(meta["size"])
            md5 = meta["md5"]
            fs_id = meta["fs_id"]
            path = meta["path"][len(self.BASE_APP_PATH):]
            type_ = "File"
            mtime = meta["mtime"]
            category = category_decode(meta["category"])
            if not path.startswith("/"):
                path = "/" + path
            mtime = time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(int(mtime)))
            line = [type_, path, size, mtime, category, fs_id, md5]
            l.append(line)
        else:
            allpath = list(self._walk_remote_dir(
                remotepath=self.remotepath, recursive=False))
            if len(allpath):
                for p in allpath:
                    if p["isdir"]:
                        size = "-"
                        md5 = "-"
                        fs_id = p["fs_id"]
                        path = p["path"][len(self.BASE_APP_PATH):] + "/"
                        type_ = "Dir"
                        mtime = p["mtime"]
                        category = "-"
                    else:
                        size = human_size(p["size"])
                        md5 = p["md5"]
                        fs_id = p["fs_id"]
                        path = p["path"][len(self.BASE_APP_PATH):]
                        type_ = "File"
                        mtime = p["mtime"]
                        category = category_decode(p["category"])
                    if not path.startswith("/"):
                        path = "/" + path
                    mtime = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(int(mtime)))
                    line = [type_, path, size, mtime, category, fs_id, md5]
                    if type_.startswith("D"):
                        out = []
                        for i in line:
                            out.append(style(i, fore='blue'))
                        line = out
                    l.append(line)
            else:
                size = "-"
                md5 = "-"
                fs_id = meta["fs_id"]
                path = meta["path"][len(self.BASE_APP_PATH):] + "/"
                type_ = "Dir"
                mtime = meta["mtime"]
                category = "-"
                if not path.startswith("/"):
                    path = "/" + path
                mtime = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(int(mtime)))
                line = [type_, path, size, mtime, category, fs_id, md5]
                out = []
                for i in line:
                    out.append(style(i, fore='blue'))
                l.append(out)
                print("Empty directory: %s" % style(path, fore='blue'))
        l = sorted(l, key=lambda x: (x[0], x[3], x[2]))
        tb = prettytable.PrettyTable()
        header = []
        for i in ["type", "path", "size", "mtime", "category", "fsid", "md5"]:
            header.append(style(i, mode='bold'))
        tb.field_names = header
        for line in l:
            tb.add_row(line)
        print(tb)


class BPruner(object):

    def __init__(self, args, auth):
        self.auth = auth
        self.args = args
        auth.isLogin(msg="please login.")
        auth.login()

    @property
    def info(self):
        bp = Bpan(self.auth.token["access_token"])
        bp.info()

    @property
    def list(self):
        remotepath = self.args.path
        bp = Bpan(self.auth.token["access_token"])
        bp.remote_path_info(remotepath, bind=True)
        bp.list()

    ls = list

    @property
    def download(self):
        remotepath = self.args.input
        localdir = self.args.outdir
        bp = Bpan(self.auth.token["access_token"])
        bp.remote_path_info(remotepath, bind=True)
        bp.download(localdir, nt=self.args.threads)
