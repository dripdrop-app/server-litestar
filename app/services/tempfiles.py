import asyncio
import shutil
from pathlib import Path

import aiofiles
import aiofiles.os

TEMP_DIRECTORY = "temp"


async def cleanup_temp_directory():
    await asyncio.to_thread(shutil.rmtree, TEMP_DIRECTORY)


async def create_temp_directory():
    try:
        await aiofiles.os.mkdir(TEMP_DIRECTORY)
    except FileExistsError:
        pass


async def create_new_directory(directory: str):
    directory_path = Path(TEMP_DIRECTORY).resolve().joinpath(Path(directory))
    await create_temp_directory()
    try:
        await aiofiles.os.mkdir(directory_path)
    except FileExistsError:
        pass
    return directory_path
