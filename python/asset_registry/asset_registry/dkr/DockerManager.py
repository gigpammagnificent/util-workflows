import docker
from docker.models.images import RegistryData,Image

class DockerManager:
    def __init__(self) -> None:
        super().__init__()
        self._docker = docker.from_env()
        self._retries = 5

    def get_image_registry_data(self, image: str) -> RegistryData or None:
        attempt = 1
        while (attempt<=self._retries):
            try:
                return self._docker.images.get_registry_data(image)
            except:
                attempt = attempt+1
        return None

    def pull_image(self, image: str) -> Image or None:
        attempt = 1
        while (attempt<=self._retries):
            try:
                return self._docker.images.pull(image)
            except:
                attempt = attempt+1
        return None
