#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_send1 import Ui_MainWindow
from ui_add_account import Ui_Dialog_Account
from ui_progress import Ui_Dialog_Progress
from main import UIInterface, UITimer
from main import Account

# import pdb; pdb.set_trace()


# ################################ GUI定时器(一次性与周期性混合) ##############################
class GUITimer(UITimer, QTimer):

    def __init__(self, parent=None):
        UITimer.__init__(self)
        QTimer.__init__(self, parent)
        self._FirstSet = None
        self._Period = None
        self._Callback = None

    def setup(self, period_time, callback_function, first_set_time=None):
        if first_set_time is None:
            self._FirstSet = period_time
        else:
            self._FirstSet = first_set_time
        self._Period = period_time
        self._Callback = callback_function
        self.connect(self, SIGNAL("timeout()"), self.__iner_callback)

    def start(self, first_set_time=None):
        if first_set_time is not None:
            self._FirstSet = first_set_time
        QTimer.start(self, self._FirstSet)

    def set_tmp_time(self, tmp_time):
        self.setInterval(tmp_time)

    def stop(self):
        QTimer.stop(self)

    def __iner_callback(self):
        QTimer.setInterval(self, self._Period)
        self._Callback()


# #####################################################################
# ########################### 主窗口 ###################################
class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, gui_proc=None, parent=None):
        super(MainWindow,self).__init__(parent)
        self._GUIProc = gui_proc
        self.setupUi(self)

        # 窗口启动
        self.timer_form_load = QTimer(self)
        self.timer_form_load.setSingleShot(True)
        self.connect(self.timer_form_load, SIGNAL("timeout()"), self.slot_form_load)
        self.timer_form_load.start(200)

        # 打开正文、附件、Excel
        self.connect(self.pushButton_body, SIGNAL("clicked()"), self.slot_open_body)
        self.connect(self.pushButton_append, SIGNAL("clicked()"), self.slot_open_appends)
        self.connect(self.pushButton_mail_list, SIGNAL("clicked()"), self.slot_open_mail_list)

        # 按钮 开始、退出
        self.connect(self.pushButton_OK, SIGNAL("clicked()"), self.slot_button_run)
        self.connect(self.pushButton_cancel, SIGNAL("clicked()"), self.slot_button_cancel)

        # 添加/删除账户
        self.connect(self.pushButton_account_add, SIGNAL("clicked()"), self.account_add)
        self.connect(self.pushButton_account_del, SIGNAL("clicked()"), self.account_del)

        # 用户界面数据
        self._sub = u""
        self._body_path = u""
        self._append_list = []
        self._xls_path = u""
        self._xls_selected_list = []
        self._xls_col_name = ""
        self._sender_name = u""
        self._speed_each_hour = 400
        self._speed_each_time = 40
        self._account_list = []

    def slot_open_body(self):
        self.label_body.setText(QString(u"载入时间较长，请稍等..."))
        s = QFileDialog.getOpenFileName(self, "Open file dialog", "/", "Text file(*.txt)")
        if len(s) == 0:
            self._body_path = u""
        else:
            self._body_path = unicode(s)
        self.label_body.setText(QString(s))

    def slot_open_appends(self):
        self.label_append.setText(QString(u"载入时间较长，请稍等..."))
        s_list = QFileDialog.getOpenFileNames(self, "Open file dialog", "/", "All files(*.*)")
        if not s_list:
            self.label_append.setText(QString(u""))
            self._append_list = []
        # 拼接附件文件名
        self._append_list = [unicode(s_list[0])]
        q_s = QString(unicode(s_list[0]).replace(u'\\', u'/'))
        for i in range(1, len(s_list)):
            self._append_list.append(unicode(s_list[i]))
            q_s += QString(u"; ") + QString(unicode(s_list[i]).replace(u'\\', u'/'))
        self.label_append.setText(q_s)

    def slot_open_mail_list(self):
        self.label_maillist.setText(QString(u"载入时间较长，请稍等..."))
        s = QFileDialog.getOpenFileName(self, "Open file dialog", "/", "Excel file(*.xls;*.xlsx)")
        if len(s) == 0:
            self._xls_path = u""
        else:
            self._xls_path = unicode(s)
        self.label_maillist.setText(QString(s))

    def slot_form_load(self):
        print time.strftime('%Y-%m-%d %H:%M:%S')
        print("The form has loaded")
        # 【【【【调用GUI的事件处理函数: 窗口启动】】】】
        if self._GUIProc is not None:
            self._GUIProc.event_form_load()

    def slot_button_cancel(self):
        box = QMessageBox(self)
        box.setWindowTitle(u"Are you sure to exit?")
        b_save = box.addButton(QString(u"保存"), QMessageBox.ActionRole)
        b_discard = box.addButton(QString(u"不保存"), QMessageBox.ActionRole)
        box.addButton(QString(u"点错了"), QMessageBox.ActionRole)
        box.setText(QString(u"是否保存进度，以便下次启动继续?"))
        box.exec_()

        button = box.clickedButton()
        if button == b_save:
            print(u"Exit and save.\n")
            self._GUIProc.event_main_exit_and_save()
            self.close()
        elif button == b_discard:
            print(u"Exit and discard.\n")
            self._GUIProc.event_main_exit_and_discard()
            self.close()

    def _set_account_list_sender_name(self, sender_name):
        # 返回一个账户结构体的列表，没有则返回[]
        for i in range(len(self._account_list)):
            self._account_list[i].sender_name = sender_name

    def _ui_data_check(self):
        if len(unicode(self.lineEdit_Sub.text())) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入标题"))
            return False
        if len(self._body_path) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入正文txt文件所在路径"))
            return False
        if len(self._xls_path) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入包含邮箱列表的Excel表格所在路径"))
            return False

        start_str = unicode(self.lineEdit_Xls_From.text())
        end_str = unicode(self.lineEdit_Xls_To.text())
        if len(start_str) == 0 or len(end_str) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入Excel表格中从表的起始"))
            return False
        col_str = unicode(self.lineEdit_Xls_Col.text())
        if len(col_str) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入Excel表格中邮箱所在的列"))
            return False

        if start_str.isdigit() and end_str.isdigit() and len(col_str) == 1 \
           and col_str.isalpha() and 1 <= int(start_str) <= int(end_str) <= 100:
            pass
        else:
            QMessageBox.critical(self, u"Input Error", QString(u"请正确输入Excel表格中从表的起始及列名"))
            return False

        if len(unicode(self.lineEdit_Sender_Name.text())) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入发件人"))
            return False

        if self.listWidget.count() == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输添加发送账号"))
            return False

        return True

    def slot_button_run(self):
        if not self._ui_data_check():
            return

        self._sub = unicode(self.lineEdit_Sub.text())
        # xls表格位置选择
        start = int(self.lineEdit_Xls_From.text())
        end = int(self.lineEdit_Xls_To.text())
        self._xls_selected_list = range(start, end + 1)
        self._xls_col_name = unicode(self.lineEdit_Xls_Col.text())
        self._sender_name = unicode(self.lineEdit_Sender_Name.text())
        self._speed_each_hour = self.spinBox_Each_Hour.value()
        self._speed_each_time = self.spinBox_Each_Time.value()
        self._set_account_list_sender_name(self._sender_name)
        print(u"sub = {}\nbody_path = {}\nappend_list = {}\npath_xls = {}".format(self._sub, self._body_path, self._append_list, self._xls_path))
        print(u"selected = {}, col_name = {}, sender_name = {}".format(self._xls_selected_list, self._xls_col_name, self._sender_name))
        print(u"Speed each hour = {}, each time = {}".format(self._speed_each_hour, self._speed_each_time))
        for i, account in enumerate(self._account_list):
            print(u"Account[{}] = {}".format(i, account))

        if self._GUIProc is not None:
            # 【【【【调用GUI的事件处理函数: 开始发送】】】】
            self._GUIProc.event_start_send()

    def account_add(self):
        # 弹出添加账户界面
        new_win = AccountWindow(self)
        if not new_win.exec_():
            print(u"User cancel")
            return
        for account in self._account_list:
            if account.user == new_win.user:
                QMessageBox.critical(self, u"Input Error", QString(u"已存在该账户，要添加请先删除"))
                return
        self._account_list.append(Account(new_win.user, new_win.passwd, new_win.host, u""))
        self.listWidget.addItem(QString(new_win.user))

    def account_del(self):
        user_del = unicode(self.listWidget.item(self.listWidget.currentRow()).text())
        for i, account in enumerate(self._account_list):
            if account.user == user_del:
                del(self._account_list[i])
                break
        self.listWidget.takeItem(self.listWidget.currentRow())


# #######################################################################################
# ################################ GUI主流程 启动及事件处理 ################################
# #######################################################################################
class GUIMain(UIInterface, MainWindow):

    def __init__(self, parent=None):
        UIInterface.__init__(self)
        MainWindow.__init__(self, self)
        self.event_init_ui_timer(GUITimer(self))
        self._progress_win = None

    def proc_err_same_program(self):
        QMessageBox.critical(self, u"Program Error", QString(u"已经有另一个相同的程序在运行！\n请先停止该程序"))
        self.close()

    def proc_err_before_load(self, err, err_info):
        QMessageBox.critical(self, u"Fatal Error", QString(err_info))
        self.close()

    def proc_ask_if_recover(self, last_success_num, last_failed_num, last_not_sent):
        ret = False
        box = QMessageBox(self)
        box.setWindowTitle(u"Recover or not")
        b_recover = box.addButton(QString(u"继续上次的"), QMessageBox.ActionRole)
        box.addButton(QString(u"重新来过"), QMessageBox.ActionRole)

        box.setText(QString(u"检测到上次退出的发送情况:\n"
                            u"成功{}，  失败{}，  未发送{}\n"
                            u"要载入上次的进度吗？已发送的邮件不会再发送".format(
                             last_success_num, last_failed_num, last_not_sent)))
        box.exec_()

        button = box.clickedButton()
        if button == b_recover:
            ret = True
            print(u"User cancel recover")
        else:
            print(u"The progress will recover")
        return ret

    def proc_reload_tmp_data_to_ui(self, data):
        self._sub = data["Sub"]
        self.lineEdit_Sub.setText(QString(self._sub))
        self._body_path = data["Body"]
        self.label_body.setText(QString(self._body_path))

        self._append_list = data["AppendList"][:]
        append_str = u";".join(self._append_list)
        append_str = append_str.replace("\\", "/")
        self.label_append.setText(QString(append_str))

        self._xls_path = data["XlsPath"]
        self.label_maillist.setText(QString(self._xls_path))
        self._xls_col_name = data["ColName"]
        self.lineEdit_Xls_Col.setText(QString(self._xls_col_name))

        self._xls_selected_list = data["SelectedList"][:]
        sec_min = self._xls_selected_list[0]
        sec_max = self._xls_selected_list[-1]
        self.lineEdit_Xls_From.setText(QString(unicode(sec_min)))
        self.lineEdit_Xls_To.setText(QString(unicode(sec_max)))

        self._speed_each_hour = data["EachHour"]
        self.spinBox_Each_Hour.setValue(self._speed_each_hour)
        self._speed_each_time = data["EachTime"]
        self.spinBox_Each_Time.setValue(self._speed_each_time)

    def proc_reload_account_list_to_ui(self, account_list):
        self._account_list = account_list[:]
        for account in self._account_list:
            self.listWidget.addItem(QString(account.user))

    def proc_get_all_ui_data(self):
        data = {}
        data["Sub"], data["Body"], data["AppendList"] = self._sub, self._body_path, self._append_list[:]
        data["XlsPath"], data["ColName"] = self._xls_path, self._xls_col_name
        data["SelectedList"] = self._xls_selected_list[:]
        data["EachHour"], data["EachTime"] = self._speed_each_hour, self._speed_each_time
        data["AccountList"] = self._account_list[:]
        return data

    def proc_err_before_send(self, err, err_info):
        QMessageBox.critical(self, u"Input Error", QString(err_info))

    def proc_confirm_before_send(self, last_success_num, last_failed_num, will_send_num, all_sheets, select_list):
        info1 = u"本次将发送邮件{}封，已为您跳过邮件{}封，\n".format(will_send_num, last_success_num)
        info2 = u"以下表格的邮箱将被发送:\n"
        selected_sheets = []
        for i in select_list:
            selected_sheets.append(all_sheets[i])
        info_sheets = u"\n".join(selected_sheets)
        info3 = u"\n\n您确定要继续吗？"

        button = QMessageBox.question(self, u"Confirm",
                                      QString(info1 + info2 + info_sheets + info3),
                                      QMessageBox.Ok | QMessageBox.Cancel,
                                      QMessageBox.Ok)
        if button == QMessageBox.Ok:
            return True
        print(u"User cancel before send.")
        return False

    def proc_exec_progress_window(self):
        # 弹出进度条界面
        self._progress_win = ProgressWindow(self)
        if self._progress_win.exec_():
            print(u"Exit progress window normal")

    def proc_update_progress(self, progress_tuple=None, progress_info=None):
        # 更新进度条窗口上的所有信息
        if progress_tuple is not None:
            self._progress_win.set_progress_bar(progress_tuple[0], progress_tuple[1], progress_tuple[2])
        if progress_info is not None:
            self._progress_win.progress_log(progress_info + u"\n")

    def proc_finish_with_failed(self, success_num, failed_num, not_sent_num):
        self._progress_win.set_button_text_finish()

    def proc_finish_all_success(self, success_num, failed_num, not_sent_num):
        self._progress_win.set_button_text_finish()

    def proc_err_fatal_run(self, err, err_info):
        self._progress_win.exit_with_error(unicode(err_info))


# ########################### 添加账户窗口 ############################
class AccountWindow(QDialog, Ui_Dialog_Account):
    def __init__(self, parent=None):
        super(AccountWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)

        # 确定/取消按钮
        self.connect(self.pushButton, SIGNAL("clicked()"), self.add_account)
        self.connect(self.pushButton_cancel, SIGNAL("clicked()"), self.cancel_account)

        # 账户数据
        self.user = u""
        self.passwd = u""
        self.host = u""

    def add_account(self):
        user = unicode(self.lineEdit_user.text())
        passwd = unicode(self.lineEdit_passwd.text())
        host = unicode(self.lineEdit_host.text())

        if len(user) == 0 or len(passwd) == 0 or len(host) == 0:
            QMessageBox.critical(self, u"Input Error", QString(u"请输入完整信息"))
            return

        if -1 == user.find(u"@"):
            QMessageBox.critical(self, u"Input Error", QString(u"邮箱账号有误，应为xxx@@xxx.xxx"))
            return

        self.user = user
        self.passwd = passwd
        self.host = host
        self.accept()

    def cancel_account(self):
        self.reject()


# ########################### 进度条窗口 ############################
class ProgressWindow(QDialog, Ui_Dialog_Progress):

    def __init__(self, gui_proc=None, parent=None):
        super(ProgressWindow, self).__init__(parent)
        self._GUIProc = gui_proc
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)

        # 暂停按钮
        self.connect(self.pushButton, SIGNAL("clicked()"), self.slot_pause)

    def slot_pause(self):
        if self._GUIProc is not None:
            self._GUIProc.event_user_cancel_progress()
        QMessageBox.information(self, u"Information",
                                QString(u'如果想重发已失败的邮件，可以再次点击"开始"\n已发送成功的邮件不会重复发送'))
        self.accept()  # 关闭窗口 表示用户是按暂停退出而不是直接关闭窗口

    def set_progress_bar(self, success_num, failed_num, not_sent_num):
        self.label_has_sent.setText(QString(unicode(success_num)))
        self.label_failed_sent.setText(QString(unicode(failed_num)))

        all_num = success_num + failed_num + not_sent_num
        show_num = success_num + failed_num
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(all_num)
        self.progressBar.setValue(show_num)

    def progress_log(self, content):
        self.textEdit.append(QString(unicode(content)))

    def set_button_text_finish(self):
        self.pushButton.setText(QString(u"完成"))

    def exit_with_error(self, err_info=u""):
        if err_info != u"":
            QMessageBox.critical(self, u"Fatal Error", QString(err_info))
        self.accept()

def test_ui_progress():
    app = QApplication(sys.argv)
    Window = ProgressWindow()
    Window.show()
    app.exec_()


def test_main_win():
    app = QApplication(sys.argv)
    Window = MainWindow(None)
    Window.show()
    app.exec_()


# Main Function
def main():
    QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))
    app = QApplication(sys.argv)
    Window = GUIMain(None)
    Window.show()
    app.exec_()


if __name__=='__main__':
    main()
    #test_ui_progress()
    # test_gui_timer()
