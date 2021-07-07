# Boa:Frame:FRAME2
import time
import json
import traceback
import win32con
import win32api
import pyperclip
import re
import os
import threading
import xlrd
import wx
import pyWinhook
import shutil
from pydub import AudioSegment

wx.NO_3D = 0
HOT_KEYS = ['F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']
failed_name_list = []
# 1秒=1000毫秒
SECOND = 1000


# 音频剪辑，剪去后缀 剔除的后缀的时间长度
def chunk_suffix_audio(audio_path, suffix_second=2.8, audio_type="mp3", target_path=None):
    if not (audio_path and suffix_second > 0 and audio_type):
        return False
    if not target_path:
        target_path = audio_path
    # 导入音乐
    input_music = AudioSegment.from_file(audio_path, audio_type)
    # print("audio_path=%s, len=%s" % (audio_path, len(input_music)))
    # 裁剪
    output_music = input_music[:len(input_music) - suffix_second * SECOND]
    # 导出音乐
    output_music.export(target_path)


# 重命名，多个备用方案
def rename_file(dst_file, *src_file):
    try:
        os.rename(src_file[0], dst_file)
    except Exception as e:
        print(e)
        print('rename file fail\r\n')
        if "系统找不到指定的文件" in str(e) and len(src_file) > 1:
            return rename_file(dst_file, *src_file[1:])
        else:
            return False
    else:
        print('rename file success\r\n')
        return True
    pass


def create():
    return Frame2()


def current_ts():
    return int(time.time() * 1000)


'''
    如果文件夹不存在就创建，如果文件存在就清空！
    :param filepath:需要创建的文件夹路径
    :return:
'''


def reset_folder(filepath):
    if os.path.exists(filepath):
        shutil.rmtree(filepath)
    os.mkdir(filepath)


# # 重置提示
# def reset_enter_hint(event):
#     event.GetEventObject().Label = "清空音频文件，并清空转换结果"
#     pass


class Frame2():
    def _init_ctrls(self):
        self.win = wx.Frame(None, style=wx.STAY_ON_TOP | wx.DEFAULT_FRAME_STYLE,
                            title='迅捷语音模拟点击生成', size=(450, 500))
        bkg = wx.Panel(self.win)
        '''
        前期脚本
        '''
        self.label_header_txt = wx.StaticText(bkg, label='前期txt', name='label_header_txt', style=0)
        self.text_header_txt = wx.TextCtrl(bkg,
                                           value="F:/chenguilin/worksapce/pycharm_workspace/volume_header.txt")
        self.headerButton = wx.Button(bkg, label='前期')
        self.headerButton.Bind(wx.EVT_BUTTON, self.header)
        '''
        后期脚本
        '''
        self.label_footer_txt = wx.StaticText(bkg, label='后期txt', name='label_footer_txt', style=0)
        self.text_footer_txt = wx.TextCtrl(bkg,
                                           value="F:/chenguilin/worksapce/pycharm_workspace/volume_footer.txt")
        self.footerButton = wx.Button(bkg, label='后期')
        self.footerButton.Bind(wx.EVT_BUTTON, self.footer)
        '''
        收尾脚本
        '''
        self.label_reset_txt = wx.StaticText(bkg, label='收尾txt', name='label_reset_txt', style=0)
        self.text_reset_txt = wx.TextCtrl(bkg,
                                          value="F:/chenguilin/worksapce/pycharm_workspace/volume_reset.txt")
        self.resetButton = wx.Button(bkg, label='收尾')
        self.resetButton.Bind(wx.EVT_BUTTON, self.reset)
        '''
        xls路径
        '''
        self.label_xls = wx.StaticText(bkg, label='.xls读取路径', name='label_xls_path', style=0)
        self.text_xls = wx.TextCtrl(bkg, value="F:/chenguilin/worksapce/autoRunner_workspace/1.xls")
        '''
        音频保存路径
        '''
        self.label_audio = wx.StaticText(bkg, label='.mp3保存文件夹', name='label_audio_path', style=0)
        self.text_audio = wx.TextCtrl(bkg, value="F:/chenguilin/worksapce/autoRunner_workspace/audio/")
        # 重置
        self.resetAudioFolderButton = wx.Button(bkg, label='重置路径')
        self.resetAudioFolderButton.Bind(wx.EVT_BUTTON, self.reset_audio_folder)
        '''
        各种控制--按钮
        '''
        # 启动
        self.startButton = wx.Button(bkg, label='开始生成')
        self.startButton.Bind(wx.EVT_BUTTON, self.start)
        # 清空日志
        self.clearLogButton = wx.Button(bkg, label='清空日志')
        self.clearLogButton.Bind(wx.EVT_BUTTON, self.clear_log)
        # 帮助
        self.helpButton = wx.Button(bkg, label='帮助')
        self.helpButton.Bind(wx.EVT_BUTTON, self.help)
        # self.resetButton.Bind(wx.EVT_ENTER_WINDOW, reset_enter_hint)
        '''
         各种控制--数字框
        '''
        # 读取起始索引
        self.label_start_index = wx.StaticText(bkg, label='读取起始索引', name='label_start_index', style=0)
        self.spin_start_index = wx.SpinCtrl(bkg, initial=1, max=1000, min=1, style=0)
        self.spin_start_index.SetFocus()
        # 读取条数，即最多从excel读取上限
        self.label_count = wx.StaticText(bkg, label='读取总数', name='label_count', style=0)
        self.spin_count = wx.SpinCtrl(bkg, initial=200, max=1000, min=1, style=0)
        '''
        各种控制--列表
        '''
        # 启动热键
        self.label_start_hot_key = wx.StaticText(bkg, label='启动热键', name='label_start_hot_key',
                                                 style=wx.ALIGN_CENTRE_VERTICAL)
        self.choice_start = wx.Choice(bkg, choices=[], name='choice_start', style=0)
        # 中止热键
        self.label_stop_hot_key = wx.StaticText(bkg, label='中止热键', name='label_stop_hot_key', style=wx.TE_LEFT)
        self.choice_stop = wx.Choice(bkg, choices=[], name='choice_stop', style=0)
        '''
        日志 静态文本不支持滑动块？
        '''
        # self.label_log = wx.StaticText(bkg, label='日志', name='label_log', style=wx.TE_MULTILINE | wx.VSCROLL)
        self.label_log = wx.TextCtrl(bkg, value='日志', name='label_log', style=wx.TE_MULTILINE | wx.VSCROLL)
        self.label_log.SetMinSize((450, 300))
        '''
        界面整合
        '''
        self.hbox_header_txt = self.get_hbox_with_proportion(wx
                                                             , {"view": self.label_header_txt, "proportion": 0}
                                                             , {"view": self.text_header_txt, "proportion": 1}
                                                             , {"view": self.headerButton, "proportion": 0}
                                                             )
        self.hbox_footer_txt = self.get_hbox_with_proportion(wx
                                                             , {"view": self.label_footer_txt, "proportion": 0}
                                                             , {"view": self.text_footer_txt, "proportion": 1}
                                                             , {"view": self.footerButton, "proportion": 0}
                                                             )
        self.hbox_reset_txt = self.get_hbox_with_proportion(wx
                                                            , {"view": self.label_reset_txt, "proportion": 0}
                                                            , {"view": self.text_reset_txt, "proportion": 1}
                                                            , {"view": self.resetButton, "proportion": 0}
                                                            )
        self.hbox_xls = self.get_hbox_with_proportion(wx
                                                      , {"view": self.label_xls, "proportion": 0}
                                                      , {"view": self.text_xls, "proportion": 1}
                                                      )
        self.hbox_audio = self.get_hbox_with_proportion(wx
                                                        , {"view": self.label_audio, "proportion": 0}
                                                        , {"view": self.text_audio, "proportion": 1}
                                                        , {"view": self.resetAudioFolderButton, "proportion": 0}
                                                        )
        self.hbox_control_button = self.get_hbox_with_proportion(wx
                                                                 , {"view": self.startButton, "proportion": 1}
                                                                 , {"view": self.clearLogButton, "proportion": 1}
                                                                 , {"view": self.helpButton, "proportion": 1}
                                                                 )
        self.hbox_control_choice = self.get_hbox_with_proportion(wx
                                                                 , {"view": self.choice_start, "proportion": 1}
                                                                 , {"view": self.label_start_hot_key, "proportion": 1}
                                                                 , {"view": self.choice_stop, "proportion": 1}
                                                                 , {"view": self.label_stop_hot_key, "proportion": 1}
                                                                 )
        self.hbox_control_spin = self.get_hbox_with_proportion(wx
                                                               , {"view": self.spin_start_index, "proportion": 1}
                                                               , {"view": self.label_start_index, "proportion": 1}
                                                               , {"view": self.spin_count, "proportion": 1}
                                                               , {"view": self.label_count, "proportion": 1}
                                                               )
        self.hbox_log = self.get_hbox_with_proportion(wx
                                                      , {"view": self.label_log, "proportion": 1}
                                                      )
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.hbox_header_txt, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_footer_txt, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_reset_txt, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_xls, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_audio, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_control_button, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_control_choice, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_control_spin, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.hbox_log, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)
        bkg.SetSizer(self.vbox)
        pass

    def __init__(self):
        #
        self._init_ctrls()
        #
        self.choice_start.SetItems(HOT_KEYS)
        self.choice_start.SetSelection(3)
        #
        self.choice_stop.SetItems(HOT_KEYS)
        self.choice_stop.SetSelection(6)
        #
        self.running = False

        def on_keyboard_event(event):
            message = event.MessageName
            message = message.replace(' sys ', ' ')
            # print('message=%s, running=%s' % (message, self.running))
            if message == 'key up':
                key_name = event.Key.lower()
                start_index = self.choice_start.GetSelection()
                stop_index = self.choice_stop.GetSelection()
                start_name = HOT_KEYS[start_index].lower()
                stop_name = HOT_KEYS[stop_index].lower()
                # print('key_name=%s, start_name=%s, stop_name=%s' % (key_name, start_name,  stop_name))
                if key_name == stop_name and self.running:
                    self.running = False
                    print('break exit!')
                    print("失败列表：{0}".format(failed_name_list))
                    self.append_log_lines("中止流程中，请等待结束日志")
                    self.append_log_lines("失败列表：{0}".format(failed_name_list))
                    # 停止程序
                    # os._exit(0)
                elif key_name == start_name and not self.running:
                    self.start(event)
            return True

        self.hm = pyWinhook.HookManager()
        self.hm.KeyAll = on_keyboard_event
        self.hm.HookKeyboard()

    # 前期
    def header(self, event):
        script_path_header = self.get_header_txt_path()
        content_header = self.get_script_by_path(script_path_header)
        if not (content_header and content_header != ""):
            self.append_log_lines('\n请输入有效前期脚本')
            return
        self.run_script_by_content(content_header)
        pass

    # 后期
    def footer(self, event):
        script_path_footer = self.get_footer_txt_path()
        content_footer = self.get_script_by_path(script_path_footer)
        if not (content_footer and content_footer != ""):
            self.append_log_lines('\n请输入有效后期脚本')
            return
        self.run_script_by_content(content_footer)
        pass

    # 收尾
    def reset(self, event):
        script_path_reset = self.get_reset_txt_path()
        content_reset = self.get_script_by_path(script_path_reset)
        if not (content_reset and content_reset != ""):
            self.append_log_lines('\n请输入有效收尾脚本')
            return
        self.run_script_by_content(content_reset)
        pass

    def help(self, event):
        self.show('注意事项：'
                  + '\n1、每次要手动打开应用，打开后对窗口的位置和宽高不要有任何更改；'
                  + '\n2、应用设置，音量：10，语速：6，保存路径与定义的语音保存文件夹一致；'
                  + '\n3、尽量使数据源没有重名，名称中的"/"等特殊符号已在程序中过滤，但存在某些特殊符号仍需手动剔除，以免更改文件名失败'
                    '，应用生成的文件名存在误差时导致更改文件名失败，可手动更改；'
                  + '\n4、重复操作时需重新打开应用，以免应用本身创建重复数据源时添加诸如“（2）、（3）”等副本后缀导致更改文件名失败'
                    '，程序单次收尾能自适应最多4次相同副本后缀，或者可使用收尾按钮清空生成记录；'
                  + '\n5、根据xls文件中列名包含“名称”作为语音文字，列名包含“编号”作为文件保存重命名并且自动前缀补0至3位，如001.mp3、123.mp3；'
                  + '\n')

    def reset_audio_folder(self, event):
        audio_path = self.get_audio_path()
        if not (audio_path and audio_path != ""):
            self.append_log_lines('\n请输入.mp3路径')
            return
        reset_folder(audio_path)

    def clear_log(self, event):
        self.label_log.SetLabel('日志')
        pass

    def start(self, event):
        self.clear_log(event)
        t = RunScriptClass(self, threading.Event())
        t.start()
        event.Skip()

    def append_log_lines(self, msg):
        if msg:
            # self.label_log.SetLabel(self.get_log() + "\n" + str(msg))
            self.label_log.SetValue(self.get_log() + "\n" + str(msg))
            # 滑动到底部
            self.label_log.ScrollLines(self.label_log.GetNumberOfLines())

    def append_log(self, msg):
        if msg:
            # self.label_log.SetLabel(self.get_log() + str(msg))
            self.label_log.SetValue(self.get_log() + str(msg))
            self.label_log.ScrollLines(self.label_log.GetNumberOfLines())

    def show(self, msg):
        if msg:
            # self.label_log.SetLabel(msg)
            self.label_log.SetValue(msg)
            self.label_log.ScrollLines(self.label_log.GetNumberOfLines())

    def get_log(self):
        # return self.label_log.GetLabel()
        return self.label_log.Value

    def get_header_txt_path(self):
        return self.text_header_txt.Value

    def get_footer_txt_path(self):
        return self.text_footer_txt.Value

    def get_reset_txt_path(self):
        return self.text_reset_txt.Value

    def get_xls_path(self):
        return self.text_xls.Value

    def get_audio_path(self):
        return self.text_audio.Value

    def get_max_count(self):
        return self.spin_count.Value

    def set_start_index(self, start_index):
        self.spin_start_index.SetValue(start_index)

    def get_start_index(self):
        return self.spin_start_index.Value

    # 横向居左对齐布局
    def get_hbox_with_proportion(self, wx, *dict_list):
        hbox = wx.BoxSizer()
        for dict in dict_list:
            hbox.Add(dict.get("view"), proportion=dict.get("proportion"), flag=wx.LEFT, border=5)
        return hbox

    def get_script_by_path(self, script_path):
        content = ''

        lines = []

        try:
            lines = open(script_path, 'r', encoding='utf8').readlines()
        except Exception as e:
            print(e)
            try:
                lines = open(script_path, 'r', encoding='gbk').readlines()
            except Exception as e:
                print(e)

        for line in lines:
            # 去注释
            if '//' in line:
                index = line.find('//')
                line = line[:index]
            # 去空字符
            line = line.strip()
            content += line

        # 去最后一个元素的逗号（如有）
        content = content.replace('],\n]', ']\n]').replace('],]', ']]')
        return content

    def run_script_by_content(self, content, thd=None):
        s = json.loads(content)
        steps = len(s)

        sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        for i in range(steps):

            print(s[i])

            delay = s[i][0]
            event_type = s[i][1].upper()
            message = s[i][2].lower()
            action = s[i][3]

            time.sleep(delay / 1000.0)

            if thd:
                current_status = thd.frame.tnumrd.GetLabel()
                if current_status in ['broken', 'finished']:
                    break
                thd.event.wait()
                text = '%s  [%d/%d %d/%d]' % (thd.running_text, i + 1, steps, thd.j, thd.run_times)
                thd.frame.tnumrd.SetLabel(text)

            if event_type == 'EM':
                x, y = action

                if action == [-1, -1]:
                    # 约定 [-1, -1] 表示鼠标保持原位置不动
                    pass
                else:
                    # 挪动鼠标 普通做法
                    # ctypes.windll.user32.SetCursorPos(x, y)
                    # or
                    # win32api.SetCursorPos([x, y])

                    # 更好的兼容 win10 屏幕缩放问题
                    nx = int(x * 65535 / sw)
                    ny = int(y * 65535 / sh)
                    win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE | win32con.MOUSEEVENTF_MOVE, nx, ny, 0, 0)

                if message == 'mouse left down':
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                elif message == 'mouse left up':
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                elif message == 'mouse right down':
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                elif message == 'mouse right up':
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                elif message == 'mouse move':
                    pass
                else:
                    print('unknow mouse event:', message)

            elif event_type == 'EK':
                key_code, key_name, extended = action

                # shift ctrl alt
                # if key_code >= 160 and key_code <= 165:
                #     key_code = int(key_code/2) - 64

                base = 0
                if extended:
                    base = win32con.KEYEVENTF_EXTENDEDKEY

                if message == 'key down':
                    win32api.keybd_event(key_code, 0, base, 0)
                elif message == 'key up':
                    win32api.keybd_event(key_code, 0, base | win32con.KEYEVENTF_KEYUP, 0)
                else:
                    print('unknow keyboard event:', message)

            elif event_type == 'EX':

                if message == 'input':
                    text = action
                    pyperclip.copy(text)
                    # Ctrl+V
                    win32api.keybd_event(162, 0, 0, 0)  # ctrl
                    win32api.keybd_event(86, 0, 0, 0)  # v
                    win32api.keybd_event(86, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(162, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    print('unknow extra event:', message)
        pass


# 查找、重命名
def find_rename_file(dir_path, file_rename, file_src_name):
    for root, dirs, files in os.walk(dir_path):
        print(files)
        for file in files:
            if file_src_name in file:
                if rename_file(file_rename, dir_path + file):
                    return True
                else:
                    return False


class RunScriptClass(threading.Thread):

    def __init__(self, frame: Frame2, event: threading.Event):
        self.frame = frame
        self.event = event
        self.event.set()
        super(RunScriptClass, self).__init__()

    def run(self):
        if self.frame.running:
            return
        #
        xls_path = self.frame.get_xls_path()
        audio_path = self.frame.get_audio_path()
        max_count = self.frame.get_max_count()
        script_path_header = self.frame.get_header_txt_path()
        script_path_footer = self.frame.get_footer_txt_path()
        script_path_reset = self.frame.get_reset_txt_path()
        audio_suffix = "-迅捷文字转语音"
        print("xls_path=%s, \naudio_path=%s, \nmax_count=%s " % (xls_path, audio_path, max_count))
        self.frame.append_log_lines("xls_path=%s, \naudio_path=%s, \nmax_count=%s " % (xls_path, audio_path, max_count))
        # 前期
        content_header = self.frame.get_script_by_path(script_path_header)
        # 后期
        content_footer = self.frame.get_script_by_path(script_path_footer)
        # 重置
        content_reset = self.frame.get_script_by_path(script_path_reset)
        # 起始索引
        start_index = self.frame.get_start_index() - 1
        #
        error_msg = ""
        if not (xls_path and xls_path != ""):
            error_msg += '\n请输入.xls读取路径'

        if not (audio_path and audio_path != ""):
            error_msg += '\n请输入.mp3保存路径'

        if not (max_count > 0 and max_count < 1001):
            error_msg += '\n请输入合法最大读取条数'

        if not (content_header and content_header != ""):
            error_msg += '\n请输入有效前期脚本'

        if not (content_footer and content_footer != ""):
            error_msg += '\n请输入有效后期脚本'

        if not (content_reset and content_reset != ""):
            error_msg += '\n请输入有效收尾脚本'
        print("error_msg=%s" % error_msg)
        if error_msg and error_msg != "":
            self.frame.append_log_lines(error_msg)
            return
        #
        self.frame.running = True
        #
        try:
            failed_name_list = []
            self.frame.append_log_lines("开始")
            self.read_excel_run_script(xls_path, content_header, content_footer, content_reset, audio_path,
                                       audio_suffix, start_index, max_count)
            print('script run finish!')
        except Exception as e:
            print('run error', e)
            traceback.print_exc()
            self.frame.append_log_lines('异常')
        finally:
            self.frame.running = False
            self.frame.append_log_lines('结束')

    def run_script_once(self, script_path, thd=None):

        content = self.frame.get_script_by_path(script_path)

        print(content)

        self.frame.run_script_by_content(content, thd)

    # 从excel中读取作为core并装载拼接运行
    def read_excel_run_script(self, excel_path, content_header, content_footer, content_reset, audio_folder,
                              audio_suffix, start_index=0, max_count=5):

        # F9中断并打印一失败列表：名称_编号
        # 获取excel列值
        book = xlrd.open_workbook(excel_path)
        name_col_index = 0
        number_col_index = 0
        name_list = []
        number_list = []
        # 名称、编号
        for sheet in book.sheets():
            header_rows = sheet.row_values(0)
            for i in range(len(header_rows)):
                if "名称" in header_rows[i]:
                    name_col_index = i
                elif "编号" in header_rows[i]:
                    number_col_index = i
            #
            name_list_sheet = sheet.col_values(name_col_index)
            number_list_sheet = sheet.col_values(number_col_index)
            # 剔除第一个
            name_list.extend(name_list_sheet[-len(name_list_sheet) + 1:])
            number_list.extend(number_list_sheet[-len(number_list_sheet) + 1:])
        # 剔除符号
        strinfo = re.compile(r'[ （），。、#￥%…&*\-=——+$^(),./:|：]')
        print("last_index=%s" % start_index)
        max_count += start_index
        self.frame.append_log_lines('max_count=%s, size=%s' % (max_count, len(name_list)))
        if start_index > len(name_list):
            self.frame.append_log_lines('读取起始索引大于xls包含条目数')
        for i in range(start_index, len(name_list)):
            print("last_index={0}, name_list={1}".format(i, len(name_list)))
            # 程序中止 最大运行条数
            if not (self.frame.running and i < max_count):
                break
            name = name_list[i]
            number = number_list[i]
            self.frame.append_log_lines('name=%s, number=%s' % (name, number))
            # 前期脚本
            self.frame.run_script_by_content(content_header)
            # 核心脚本
            self.frame.run_script_by_content('[[200,  "EX","input", "' + name + '"]]')
            # 后期脚本
            self.frame.run_script_by_content(content_footer)
            # 等待文件生成
            time.sleep(0.6)
            # 迅捷先取前5位再剔除符号
            change_name = strinfo.sub('', name[0:5])
            # # 风云先剔除符号再取前4位
            # change_name = strinfo.sub('', name)[0:4]
            # 备用源文件重命名
            # src_file = audio_folder + change_name + audio_suffix + ".mp3"
            # src_file2 = audio_folder + change_name + audio_suffix + "(2).mp3"
            # src_file3 = audio_folder + change_name + audio_suffix + "(3).mp3"
            # src_file4 = audio_folder + change_name + audio_suffix + "(4).mp3"
            # src_file5 = audio_folder + change_name + audio_suffix + "(5).mp3"
            # 重命名预期文件名
            dstFile = audio_folder + ("000" + str(int(number)))[-3:] + ".mp3"
            # if not rename_file(dstFile, src_file, src_file2, src_file3, src_file4, src_file5):
            #     self.frame.append_log('----生成失败')
            #     # 记录失败列表
            #     failed_name_list.append(name + "_" + str(int(number)))
            # else:
            #     self.frame.append_log('----生成成功')
            if not find_rename_file(audio_folder, dstFile, change_name):
                self.frame.append_log('----生成失败')
                # 记录失败列表
                failed_name_list.append(name + "_" + str(int(number)))
            else:
                self.frame.append_log('----生成成功')
                chunk_suffix_audio(dstFile)
        print("失败列表：{0}".format(failed_name_list))
        self.frame.append_log_lines("失败列表：{0}".format(failed_name_list))
        self.frame.run_script_by_content(content_reset)
