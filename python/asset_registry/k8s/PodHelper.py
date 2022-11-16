from dotmap import DotMap
from kubernetes.client.models.v1_pod import V1Pod
import re

def __get_image_digest(image_id: str) -> str:
    search = re.search('^.*@(.*)$', image_id);

    return None if (search == None or len(search.groups())<1) else search.group(1)

def __get_container_info(containers, statuses):
    if (containers == None):
        return []

    container_list = []

    for container in containers:
        container_obj = {
            'name': container.name,
            'image': container.image
        }
        for status in statuses:
            if (container.name == status.name):
                container_obj["image_id"] = status.image_id
                container_obj["digest"] = __get_image_digest(status.image_id)
                break

        container_list.append(DotMap(container_obj))

    return container_list

def get_container_image_details(pod: V1Pod):

    container_list = []

    init_container_info = __get_container_info(pod.spec.init_containers, pod.status.init_container_statuses)
    container_info = __get_container_info(pod.spec.containers, pod.status.container_statuses)

    container_list.extend(init_container_info)
    container_list.extend(container_info)

    return container_list
