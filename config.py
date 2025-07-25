import os
from pathlib import Path

# ===== CẤU HÌNH =====
CHUNK_WORDS = 500
MAX_CONCURRENCY = 128
MAX_RETRIES = 3
BYTE_PER_WORD = 1280
VOICE = "vi-VN-NamMinhNeural"
DOWNLOADS = str(Path.home() / "Downloads")