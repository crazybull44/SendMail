#!/usr/bin/python
# -*- coding: utf-8 -*-

# 导入主py却不使用,初始化db,设置和启动Aupt

from autoupt import AuptMain
from main import AuptDB
import Run_GUI


def run():
    db = AuptDB()

    url_ver = r'http://git.oschina.net/mmyz/SendMail/raw/master/README.md'
    url_pkg = r'http://git.oschina.net/mmyz/SendMail/raw/master/version.zip'
    run_py, run_func = 'Run_GUI', 'main'
    aupt = AuptMain(db, url_ver, url_pkg, run_py, run_func)
    aupt.run()


if __name__ == '__main__':
    run()
