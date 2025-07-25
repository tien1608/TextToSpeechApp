import os

def is_valid(path, text, byte_per_word):
    if not os.path.exists(path): return False
    size = os.path.getsize(path)
    expected = len(text.split()) * byte_per_word
    return size >= expected


def find_invalid_files(chunks, folder, byte_per_word):
    return [i for i, c in enumerate(chunks)
            if not is_valid(os.path.join(folder, f"part_{i:03}.mp3"), c, byte_per_word)]