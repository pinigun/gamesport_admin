from fastapi import UploadFile
from filelock import AsyncFileLock
import aiofiles

class PhotoTools:
    async def save_photo(path: str, photo: UploadFile, filename: str = None):
        file_path = f'{path}/{"general" if filename is None else filename}{photo.filename.split('.')[-1]}'
        async with AsyncFileLock(f'{file_path}.lock', timeout=10):
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await photo.read())
                return file_path