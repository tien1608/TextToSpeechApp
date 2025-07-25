import os
from pydub import AudioSegment

def combine_files(mp3_files, output_path):
    combined = AudioSegment.empty()
    for file in mp3_files:
        if os.path.exists(file):
            combined += AudioSegment.from_mp3(file)
    combined.export(output_path, format="mp3")