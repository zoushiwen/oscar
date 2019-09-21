# -*- coding:utf-8 -*-


import sys



def Print(content,colour=None):
    if colour is not None:
        if colour == "red":
            print("\033[1;31m{} \033[0m".format(content))
            sys.exit(1)
        elif colour == "green":
            print("\033[1;32m{} \033[0m".format(content))
        elif colour == "yellow":
            print("\033[1;33m{} \033[0m".format(content))
        else:
            print(content)
    else:
        print(content)