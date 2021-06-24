import wx
import Frame2


def main():
    app = wx.App()
    Frame2.create().win.Show()
    app.MainLoop()


# 生成exe文件
# pyinstaller -F -w AudioAutoClick.py
if __name__ == '__main__':
    # # 读取excel方式
    # excel_path = ''
    # script_path_header = "scripts/volume_header.txt"
    # script_path_footer = "scripts/volume_footer.txt"
    # audio_folder = ""
    # audio_suffix = "-迅捷文字转语音"
    # max_count = 10000
    # failed_name_list = []
    # read_excel_run_script(excel_path, script_path_header, script_path_footer, audio_folder, audio_suffix, max_count)
    main()
