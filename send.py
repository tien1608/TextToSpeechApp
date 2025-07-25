import os
import edge_tts
import asyncio
from tqdm.asyncio import tqdm_asyncio


async def convert_chunk(index, text, folder, voice):
    path = os.path.join(folder, f"part_{index:03}.mp3")
    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(path)
    except Exception as e:
        print(f"Lỗi đoạn {index}: {e}")


async def process_chunks_async(chunks, folder, batch_indices, max_concurrency, voice):
    sem = asyncio.Semaphore(max_concurrency)

    async def process_one(i):
        async with sem:
            await convert_chunk(i, chunks[i], folder, voice)

    await tqdm_asyncio.gather(*(process_one(i) for i in batch_indices), desc="🔊 Đang xử lý", unit="đoạn")
