import sys

from .src import *


def main():
    log = loger()
    args = parseArg()
    auth = Authorization()
    if args.mode == "login":
        auth.login(force=True)
        log.info("login success")
        bp = Bpan(auth.token["access_token"])
        bp.info()
    elif args.mode == "logout":
        if not auth.isLogin():
            log.info("no account for logout.")
        else:
            auth.logout()
            log.info("logout success.")
    elif args.mode == "info":
        auth.isLogin(msg="please login.")
        auth.login()
        bp = Bpan(auth.token["access_token"])
        bp.info()
    elif args.mode in ["list", "ls"]:
        auth.isLogin(msg="please login.")
        auth.login()
        remotepath = args.path
        bp = Bpan(auth.token["access_token"])
        bp.remote_path_info(remotepath, bind=True)
        bp.list()
    elif args.mode == "download":
        if not os.path.isfile(auth.token_file):
            log.error("please login.")
            sys.exit(1)
        remotepath = args.input
        localdir = args.outdir
        auth.isLogin(msg="please login.")
        auth.login()
        bp = Bpan(auth.token["access_token"])
        bp.remote_path_info(remotepath, bind=True)
        np = args.nproc or 0
        bp.download(localdir, nt=args.threads, np=np)


if __name__ == "__main__":
    main()
