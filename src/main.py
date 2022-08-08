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
    for actions in ["info", "ls", "list", "download"]:
        if args.mode == actions:
            bprun = BPruner(args, auth)
            getattr(bprun, actions)


if __name__ == "__main__":
    main()
