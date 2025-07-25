import asyncio
import os
import shutil
from pathlib import Path
from tkinter import Tk, filedialog

from config import *
from read import read_pdf, read_docx, split_text, save_chunks
from send import process_chunks_async
from checkerrorfile import find_invalid_files
from finalmp3 import combine_files


def choose_file():
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilename(filetypes=[("Document", "*.pdf *.docx")])


async def main():
    path = choose_file()
    if not path:
        print("Không chọn file.")
        return

    base = Path(path).stem
    temp_dir = os.path.join(DOWNLOADS, f"{base}_temp")
    final_mp3 = os.path.join(DOWNLOADS, f"{base}.mp3")

    print("Đang đọc file...")
    if path.endswith(".pdf"):
        text = read_pdf(path)
    elif path.endswith(".docx"):
        text = read_docx(path)
    else:
        print("Chỉ hỗ trợ PDF/DOCX.")
        return

    chunks = split_text(text, CHUNK_WORDS)
    print(f"Chia thành {len(chunks)} đoạn.")
    save_chunks(chunks, temp_dir)

    await process_chunks_async(chunks, temp_dir, list(range(len(chunks))), MAX_CONCURRENCY, VOICE)

    for attempt in range(1, MAX_RETRIES + 1):
        errors = find_invalid_files(chunks, temp_dir, BYTE_PER_WORD)
        if not errors:
            break
        print(f"❌ Lần thử {attempt}: còn {len(errors)} đoạn lỗi. Gửi lại...")
        await process_chunks_async(chunks, temp_dir, errors, MAX_CONCURRENCY, VOICE)

    final_errors = find_invalid_files(chunks, temp_dir, BYTE_PER_WORD)
    if final_errors:
        print(f"\n‼️ Sau {MAX_RETRIES} lần thử vẫn còn lỗi ở các đoạn: {final_errors}")
        retry_input = input("Bạn có muốn nhập các đoạn tùy ý để gửi lại không? (vd: 0,5,7) (Enter để bỏ qua): ").strip()
        if retry_input:
            try:
                manual_indices = [int(i.strip()) for i in retry_input.split(",") if i.strip().isdigit()]
                await process_chunks_async(chunks, temp_dir, manual_indices, MAX_CONCURRENCY, VOICE)
            except Exception as e:
                print(f"Lỗi khi nhập: {e}")

    print("🎧 Đang ghép file...")
    mp3_files = [os.path.join(temp_dir, f"part_{i:03}.mp3") for i in range(len(chunks))]
    combine_files(mp3_files, final_mp3)

    shutil.rmtree(temp_dir)
    print(f"\n✅ Hoàn tất! File lưu tại: {final_mp3}")


if __name__ == "__main__":
    asyncio.run(main())
