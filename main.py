import os
import asyncio
import edge_tts
import fitz
from docx import Document
from pydub import AudioSegment
from pathlib import Path
from tkinter import Tk, filedialog
from tqdm.asyncio import tqdm_asyncio
import shutil

# ===== CẤU HÌNH =====
CHUNK_WORDS = 500
MAX_CONCURRENCY = 128
MAX_RETRIES = 3
BYTE_PER_WORD = 1280
VOICE = "vi-VN-NamMinhNeural"

DOWNLOADS = str(Path.home() / "Downloads")

# ===== Đọc file =====
def read_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

def read_docx(path):
    doc = Document(path)
    return " ".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

# ===== Chia văn bản =====
def split_text(text, chunk_words=CHUNK_WORDS):
    words = text.split()
    return [" ".join(words[i:i+chunk_words]) for i in range(0, len(words), chunk_words)]

# ===== Lưu tạm đoạn văn bản =====
def save_chunks(chunks, folder):
    os.makedirs(folder, exist_ok=True)
    for i, chunk in enumerate(chunks):
        with open(os.path.join(folder, f"text_{i:03}.txt"), "w", encoding="utf-8") as f:
            f.write(chunk)

def load_chunks(folder):
    chunks = []
    i = 0
    while True:
        path = os.path.join(folder, f"text_{i:03}.txt")
        if not os.path.exists(path):
            break
        with open(path, "r", encoding="utf-8") as f:
            chunks.append(f.read())
        i += 1
    return chunks

# ===== Kiểm tra file âm thanh =====
def is_valid(path, text):
    if not os.path.exists(path): return False
    size = os.path.getsize(path)
    expected = len(text.split()) * BYTE_PER_WORD
    return size >= expected

# ===== Chuyển đoạn sang mp3 =====
async def convert_chunk(index, text, folder):
    path = os.path.join(folder, f"part_{index:03}.mp3")
    try:
        communicate = edge_tts.Communicate(text, voice=VOICE)
        await communicate.save(path)
    except Exception as e:
        print(f"Lỗi đoạn {index}: {e}")

# ===== Ghép file mp3 =====
def combine_files(mp3_files, output_path):
    combined = AudioSegment.empty()
    for file in mp3_files:
        if os.path.exists(file):
            combined += AudioSegment.from_mp3(file)
    combined.export(output_path, format="mp3")

# ===== Hộp chọn file =====
def choose_file():
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilename(filetypes=[("Document", "*.pdf *.docx")])

# ===== Gửi các đoạn song song =====
async def process_chunks_async(chunks, folder, batch_indices):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def process_one(i):
        async with sem:
            await convert_chunk(i, chunks[i], folder)

    await tqdm_asyncio.gather(*(process_one(i) for i in batch_indices), total=len(batch_indices))

# ===== Main =====
async def main():
    path = choose_file()
    if not path:
        print("Không chọn file.")
        return

    base = Path(path).stem
    temp_dir = os.path.join(DOWNLOADS, f"{base}_temp")
    final_mp3 = os.path.join(DOWNLOADS, f"{base}.mp3")

    # Đọc văn bản
    print("Đang đọc file...")
    if path.endswith(".pdf"):
        text = read_pdf(path)
    elif path.endswith(".docx"):
        text = read_docx(path)
    else:
        print("Chỉ hỗ trợ PDF/DOCX.")
        return

    # Tách đoạn
    chunks = split_text(text)
    print(f"Chia thành {len(chunks)} đoạn.")
    save_chunks(chunks, temp_dir)

    # Gửi lần đầu
    await process_chunks_async(chunks, temp_dir, list(range(len(chunks))))

    # Gửi lại các đoạn lỗi tự động
    for attempt in range(1, MAX_RETRIES + 1):
        errors = [i for i, c in enumerate(chunks) if not is_valid(os.path.join(temp_dir, f"part_{i:03}.mp3"), c)]
        if not errors:
            break
        print(f"❌ Lần thử {attempt}: còn {len(errors)} đoạn lỗi. Gửi lại...")
        await process_chunks_async(chunks, temp_dir, errors)

    # Kiểm tra lần cuối
    final_errors = [i for i, c in enumerate(chunks) if not is_valid(os.path.join(temp_dir, f"part_{i:03}.mp3"), c)]
    if final_errors:
        print(f"\n‼️ Sau {MAX_RETRIES} lần thử vẫn còn lỗi ở các đoạn: {final_errors}")
        retry_input = input("Bạn có muốn nhập các đoạn tùy ý để gửi lại không? (vd: 0,5,7) (Enter để bỏ qua): ").strip()
        if retry_input:
            try:
                manual_indices = [int(i.strip()) for i in retry_input.split(",") if i.strip().isdigit()]
                await process_chunks_async(chunks, temp_dir, manual_indices)
            except Exception as e:
                print(f"Lỗi khi nhập: {e}")

    # Luôn ghép tất cả file
    print("🎧 Đang ghép file...")
    mp3_files = [os.path.join(temp_dir, f"part_{i:03}.mp3") for i in range(len(chunks))]
    combine_files(mp3_files, final_mp3)

    # Xoá thư mục tạm
    shutil.rmtree(temp_dir)
    print(f"\n✅ Hoàn tất! File lưu tại: {final_mp3}")

# ===== Chạy =====
if __name__ == "__main__":
    asyncio.run(main())
