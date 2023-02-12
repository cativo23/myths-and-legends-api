import os
import time

from fastapi import UploadFile

from app.core.config import settings


class ImageService:
    @staticmethod
    async def save(image: UploadFile) -> str:
        path = 'app/images/' + str(int(time.time())) + '-' + image.filename
        with open(path, 'wb') as file:
            content = await image.read()
            file.write(content)
            file.close()

        save_path = f"{settings.SERVER_HOST}:{str(settings.APP_PORT)}/api/v{settings.API_VERSION}/{path.replace('app/', '')}"

        return save_path

    @staticmethod
    def delete(image_path: str) -> bool:
        path = image_path.replace(f"{settings.SERVER_HOST}:{str(settings.APP_PORT)}/api/v{settings.API_VERSION}/", 'app/')
        print(path)
        try:
            os.remove(path)
            return True
        except OSError:
            return False


image_service = ImageService()
