from asyncio import to_thread
import os
import shutil
import aiofiles
from aiofiles.os import remove, listdir, stat
from fastapi import UploadFile
from filelock import AsyncFileLock
from pathlib import Path
from loguru import logger


async def async_path_exists(path: str) -> bool:
    try:
        await stat(path)
        return True
    except FileNotFoundError:
        return False


class PhotoTools:
    @staticmethod
    async def save_photo(path: str, photo: UploadFile, filename: str = None):
        os.makedirs(path, exist_ok=True)

        base_name = "general" if filename is None else filename
        extension = photo.filename.split('.')[-1]
        file_path = os.path.join(path, f"{base_name}.{extension}")
        lock_path = f"{file_path}.lock"

        try:
            for existing_file in await listdir(path):
                file_stem = Path(existing_file).stem
                full_path = os.path.join(path, existing_file)

                # Удаляем файлы с таким же base_name
                if file_stem == base_name:
                    try:
                        await remove(full_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить файл: {full_path}: {e}")

                # Удаляем соответствующие .lock-файлы
                if existing_file == f"{base_name}.lock":
                    try:
                        await remove(full_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить lock-файл: {full_path}: {e}")

        except Exception as e:
            print(f"Ошибка при сканировании директории {path}: {e}")

        # Сохраняем новый файл с блокировкой
        async with AsyncFileLock(lock_path, timeout=10):
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await photo.read())
                return file_path
    
    
    async def delete(path: str):
        """Асинхронно удаляет папку и всё её содержимое."""
        try:
            # shutil.rmtree не является асинхронной, оборачиваем в to_thread
            await to_thread(shutil.rmtree, path)
            logger.info(f"Папка успешно удалена: {path}")
        except FileNotFoundError:
            logger.warning(f"Папка не найдена: {path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении папки {path}: {e}")
        
        
    @staticmethod
    async def delete_file(file_path: str):
        lock_path = f"{file_path}.lock"

        try:
            async with AsyncFileLock(lock_path, timeout=10):
                # Удаление самого файла
                if await async_path_exists(file_path):
                    try:
                        await remove(file_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить файл: {file_path}: {e}")

                # Удаление lock-файла
                if await async_path_exists(lock_path):
                    try:
                        await remove(lock_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить lock-файл: {lock_path}: {e}")
        except Exception as e:
            logger.warning(f"Ошибка при попытке блокировки и удаления: {e}")