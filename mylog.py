#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
import datetime

f_Logging = None
g_check_same = None


# ####################################################################
# ########################## 日志记录模块 ##############################
class MyLog:
    """ 将标准输出/错误的内容同时复制到文件句柄中 """
    _SOURCEFILE_ENCODING = "utf-8"
    # buf记录最近打印的内容

    def __init__(self, std_fd, file_fd = None, bufsize=65536):
        if isinstance(std_fd, MyLog):
            raise Exception("The object is already mylog")
        if not isinstance(bufsize, int) or bufsize <= 0:
            raise ValueError("The bufsize %s is invalid" % repr(bufsize))
        self._std = std_fd
        self._file = file_fd
        self._bufsize = bufsize
        self._buf = ""
        self.encoding = self._std.encoding

    def closefile(self):
        if self._file is not None:
            self._file.close()

    def writefile(self, stream, is_flush = False):
        if self._file is not None:
            if isinstance(stream, str):
                self._file.write(stream)
            elif isinstance(stream, unicode):
                self._file.write(stream.encode(MyLog._SOURCEFILE_ENCODING))
            else:
                raise TypeError("The stream type is " + str(type(stream)))
            if is_flush:
                self._file.flush()

    def std(self):
        return self._std

    def buf(self):
        return self._buf

    def write(self, stream):
        self.writefile(stream, True)
        self._std.write(stream)
        # buf只保存最后bufsize个字符
        if isinstance(stream, unicode):
            stream = stream.encode(MyLog._SOURCEFILE_ENCODING)
        # 由于bufsize是按字节截取可能截断多字节的编码导致开头部分乱码
        self._buf = (self._buf + stream)[-self._bufsize:]

    def flush(self):
        if self._file is not None:
            self._file.flush()
        self._std.flush()


def mylog_reset():
    # 恢复当前标准输出(非必须)，buf会被删除
    if isinstance(sys.stdout, MyLog):
        sys.stdout.closefile()
        sys.stdout = sys.stdout.std()
    if isinstance(sys.stderr, MyLog):
        sys.stderr.closefile()
        sys.stderr = sys.stderr.std()


def mylog_set(logfile = None, bufsize=65536):
    # 设置当前标准输出/错误到文件
    # 可多次调用修改文件名, None为不输出到文件
    if not isinstance(logfile, unicode):
        try:
            unicode(logfile)
        except UnicodeDecodeError,e:
            raise Exception("The path contains Chinese must be unicode")

    if isinstance(sys.stdout, MyLog) or isinstance(sys.stderr, MyLog):
        mylog_reset()

    fd = None
    if logfile is not None:
        try:
            fd = open(logfile, "a")
        except Exception, e:
            # 打开日志文件失败，eg:日志文件可能被另一个相同的程序占用
            # 新建类似名字的文件(原文件名_openfail_时间)并留下错误信息
            filename = logfile + "_openfail_" + time.strftime("%Y%m%d_%H%M%S")
            fd = open(filename, "a")
            fd.write("Open "+logfile+" err:"+str(e)+"\n\n")
            fd.close()
            raise Exception("Open "+logfile+" err:"+str(e))

    # 重定向屏幕输出到文件fd
    sys.stdout = MyLog(sys.stdout, fd, bufsize)
    sys.stderr = MyLog(sys.stderr, fd, bufsize)


def mylog_file(stream, end='\n'):
    # 只打印到日志文件(不flush)而不打印到屏幕,不记录到buf(为保证速度)
    if isinstance(sys.stdout, MyLog):
        sys.stdout.writefile(stream + end)
    else:
        raise TypeError("The sys.stdout is not type 'mylog'")


def mylog_buf(is_stderr=False):
    # 获取标准输出/标准出错的内容 默认为标准输出
    if is_stderr:
        if isinstance(sys.stderr, MyLog):
            return sys.stderr.buf()
        else:
            raise TypeError("The sys.stderr is not type 'mylog'")
    else:
        if isinstance(sys.stdout, MyLog):
            return sys.stdout.buf()
        else:
            raise TypeError("The sys.stdout is not type 'mylog'")

######################################################################


def check_program_has_same(program_unique_port):
    global g_check_same
    ret = False
    g_check_same = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #定义socket类型，网络通信，UDP
    try:
        g_check_same.bind(("127.0.0.1", program_unique_port))          #套接字绑定的IP与端口
    except Exception, e:
        ret = True
    return ret


def check_program_has_same_fini():
    g_check_same.close()


def os_get_curr_dir():
    p = os.path.dirname(os.path.realpath(sys.argv[0]))
    p_decode = u"."
    try:
        p_decode = p.decode("gb18030")
    except Exception, e:
        print(u"Decode path of gb18030 failed:{}".format(e))
        try:
            p_decode = p.decode("utf-8")
        except Exception, e:
            print(u"Decode path of utf-8 failed:{}".format(e))
    print(u"Get MyPath = " + repr(p))

    return p_decode


def chdir_myself():
    p = os_get_curr_dir()
    if p != u".":
        os.chdir(p)
    return p


def get_time_str():
    now = datetime.datetime.now()
    time_str = now.strftime("%Y/%m/%d %H:%M:%S")
    return time_str


def print_t(log):
    time_str = get_time_str()
    content = u"\n[{}]\n{}".format(time_str, log)
    print(content)


def print_w(log):
    time_str = get_time_str()
    print(u"[{}][WARNING]\n{}".format(time_str, log))


def print_err(log):
    time_str = get_time_str()
    print(u"[{}][@@@ ERROR @@@]\n{}".format(time_str, log))


def logging_init(file_name):
    global f_Logging
    print(u"Start to init logging.")
    d = chdir_myself()
    print(u"Change dir to {}".format(repr(d)))
    log_full = os.path.join(d, file_name)
    print(u"Redirect print to {}".format(repr(log_full)))
    mylog_set(log_full)
    mylog_file(u"\n\n\n\n"+"_"*80+u"\n\n[{}] Start the program".format(get_time_str()))


def logging_fini():
    pass


def logging_init_old(file_name):
    global f_Logging
    print(u"Start to init logging.")
    d = chdir_myself()
    print(u"Change dir to {}".format(repr(d)))
    log_full = os.path.join(d, file_name)
    try:
        f_Logging = open(log_full, "a")
    except Exception, e:
        print(u"Try to write log file {} failed.".format(repr(log_full)))
        return
    else:
        print(u"Redirect the print to file.")
        sys.stdout = f_Logging
        sys.stderr = f_Logging
        print(u"\n\n\n\n" + "_"*80 + "\n")


def logging_fini_old():
    f_Logging.close()