#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
from copy import deepcopy

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui_editor import Ui_Dialog_Editor


# 装饰器：当信号来自程序设置产生时不处理
def _ignore_program_signal(func):
    def final_func(self, *args, **kwargs):
        ret = None
        if not self._is_program_signal:
            ret = func(self, *args, **kwargs)
            self.textEdit.setFocus()
        return ret
    return final_func


# 写完该类后把Ui_Dialog_Editor去掉
class BasicEditor(Ui_Dialog_Editor):

    _INIT_FONT_SIZE = 16

    # html img r'''<img\b[^<>]*?\bsrc\s*=\s*['"]?\s*([^'"<>]*)[^<>]*?/?\s*>'''
    __re_html_img = re.compile(r'''(<img\b[^<>]*?\bsrc\s*=\s*['"]?\s*)file:///([^'"<>]*)([^<>]*?/?\s*>)''')

    def __init__(self):
        super(BasicEditor, self).__init__()
        self._is_program_signal = False

    def setup_basic_editor(self):
        self._is_program_signal = False

        self.textEdit.currentCharFormatChanged.connect(self.__slot_curr_pos_fmt_changed)
        self.Button_B.clicked.connect(self.__slot_bold_press)
        self.Button_I.clicked.connect(self.__slot_italic_press)
        self.Button_U.clicked.connect(self.__slot_underline_press)
        self.fontBox.activated.connect(self.__slot_font_box_changed)
        self.fontSizeBox.valueChanged.connect(self.__slot_font_size_changed)
        self.Button_AddPic.clicked.connect(self.__slot_insert_picture)

        self.textEdit.canInsertFromMimeData = self.__can_insert_mine_data
        self.textEdit.insertFromMimeData = self.__insert_from_mine_data

        self.textEdit.setFontPointSize(self._INIT_FONT_SIZE)

    def set_html(self, html_str):
        self.textEdit.setHtml(QString(html_str))

    def to_html(self):
        return self.textEdit.toHtml()

    def __set_edit_tools_status(self, text_char_fmt):
        set_font = QFont(text_char_fmt.font())

        self._is_program_signal = True
        try:
            self.Button_B.setChecked(set_font.bold())
            self.Button_I.setChecked(set_font.italic())
            self.Button_U.setChecked(set_font.underline())
            self.fontBox.setCurrentFont(set_font)
            self.fontSizeBox.setValue(set_font.pointSize())
        finally:
            self._is_program_signal = False

    def __slot_curr_pos_fmt_changed(self, *args, **kwargs):
        # 当前光标的字体发生变化(如移动光标)
        print(u"Curr_pos_fmt_changed, set tool status")
        set_cursor = QTextCursor(self.textEdit.textCursor())

        # # 当前字体有选择文本时工具状态保持为字体发生变化时刻 已选择部分第一个字的字体
        # if set_cursor.hasSelection():
        #    set_position = min(set_cursor.position(), set_cursor.anchor()) + 1
        #    set_cursor.setPosition(set_position)

        self.__set_edit_tools_status(set_cursor.charFormat())

    @_ignore_program_signal
    def __slot_bold_press(self, *args, **kwargs):
        print(u"User pressed bold: {}".format(self.Button_B.isChecked()))
        fmt = QTextCharFormat()
        if self.Button_B.isChecked():
            fmt.setFontWeight(QFont.Bold)
        else:
            fmt.setFontWeight(QFont.Normal)
        self.__merge_format(fmt)

    @_ignore_program_signal
    def __slot_italic_press(self, *args, **kwargs):
        print(u"User pressed italic: {}".format(self.Button_I.isChecked()))
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.Button_I.isChecked())
        self.__merge_format(fmt)

    @_ignore_program_signal
    def __slot_underline_press(self, *args, **kwargs):
        print(u"User pressed underline: {}".format(self.Button_U.isChecked()))
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.Button_U.isChecked())
        self.__merge_format(fmt)

    @_ignore_program_signal
    def __slot_font_box_changed(self, *args, **kwargs):
        print(u"User font Box changed, set as new font")
        fmt = QTextCharFormat()
        user_set_font = self.fontBox.currentFont()
        fmt.setFont(user_set_font)
        self.__merge_format(fmt)

    @_ignore_program_signal
    def __slot_font_size_changed(self, *args, **kwargs):
        print(u"User font size changed to {}, set as new size".format(self.fontSizeBox.value()))
        fmt = QTextCharFormat()
        point_size = self.fontSizeBox.value()
        fmt.setFontPointSize(point_size)
        self.__merge_format(fmt)

    def __merge_format(self, fmt):
        cursor = self.textEdit.textCursor()
        cursor.mergeCharFormat(fmt)
        self.textEdit.mergeCurrentCharFormat(fmt)

    # -----------------------------------------------------------------------------------------
    # 插入图片/html
    def __slot_insert_picture(self):
        img = QImage(r'E:\MyDocuments\Python\SendMail\pic\Emotions\28.gif')
        curr_cursor = self.textEdit.textCursor()
        curr_cursor.insertImage(img)

    def __can_insert_mine_data(self, source):
        if source.hasImage():
            return True
        else:
            return QTextEdit.canInsertFromMimeData(self.textEdit, source)

    def __insert_from_mine_data(self, source):
        curr_cursor = self.textEdit.textCursor()
        if source.hasImage():
            img = QImage(source.imageData())
            curr_cursor.insertImage(img)
        elif source.hasHtml():
            modify_html = self.__html_moidfy(unicode(source.html()))
            curr_cursor.insertHtml(modify_html)

    @staticmethod
    def __html_moidfy(html_string):
        # 将用户复制粘贴的html进行处理
        return BasicEditor.__re_html_img.subn(r'\1\2\3', html_string)[0]


class WinEditor(QMainWindow, BasicEditor, Ui_Dialog_Editor):

    _TAB_INDEX_EDIT = 0
    _TAB_INDEX_HTML = 1

    def __init__(self, parent=None):
        super(WinEditor, self).__init__(parent)
        self._last_html_str = None

        self.setupUi(self)
        self.setup_basic_editor()

        # 切换到html
        self.tabWidget.currentChanged.connect(self._slot_edit_mode_change)

    # 编辑模式变化(超文本编辑/html编辑)
    def _slot_edit_mode_change(self, curr_index):

        if curr_index == self._TAB_INDEX_EDIT:
            html_str = self.PlainTextEdit_Html.toPlainText()
            if html_str != self._last_html_str:
                self.textEdit.setHtml(QString(html_str))
        elif curr_index == self._TAB_INDEX_HTML:
            html_str = QString(self.textEdit.toHtml())
            self._last_html_str = QString(html_str)
            self.PlainTextEdit_Html.setPlainText(html_str)


def main():
    QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))
    app = QApplication(sys.argv)
    win = WinEditor()
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
