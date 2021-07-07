import os
from pydub import AudioSegment

audio_path = "2.mp3"
target_path = "end_of_time_slice.mp3"
dir_path = "./audio_suffix/"
src_path = "F:/chenguilin/worksapce/autoRunner_workspace/audio/"
# 1秒=1000毫秒
SECOND = 1000

#
def chunk_suffix_audio(audio_path, suffix_second=2.8, audio_type="mp3", target_path=None):
    if not (audio_path and suffix_second > 0 and audio_type):
        return
    if not target_path:
        target_path = audio_path
    # 导入音乐
    input_music = AudioSegment.from_file(audio_path, audio_type)
    # 裁剪
    output_music = input_music[:len(input_music) - suffix_second * SECOND]
    # 导出音乐
    output_music.export(target_path)


for root, dirs, files in os.walk(src_path):
    print(files)
    for file in files:
        print(file)
        if ".mp3" in file:
            chunk_suffix_audio(src_path + file, target_path=dir_path + file)
