import asyncio
import os
import shutil

TEMP_DIRECTORY = "temp"


async def cleanup_temp_directory():
    await asyncio.to_thread(shutil.rmtree, TEMP_DIRECTORY)


async def create_temp_directory():
    try:
        await asyncio.to_thread(os.mkdir, TEMP_DIRECTORY)
    except FileExistsError:
        pass


async def create_new_directory(directory: str):
    directory_path = os.path.join(TEMP_DIRECTORY, os.path.normpath(directory))
    await create_temp_directory()
    try:
        await asyncio.to_thread(os.mkdir, directory_path)
    except FileExistsError:
        pass
    return directory_path
