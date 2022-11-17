"""asset_registry.asset_registry: provides entry point main()."""

__version__ = "1.0.0"

import argparse
from dateutil import parser
from .k8s.K8sManager import K8sManager
from .car.AssetRegistryManager import AssetRegistryManager
from .k8s import PodHelper
from .dkr.DockerManager import DockerManager

def parse_args():
    argparser = argparse.ArgumentParser(description='Update k8s Registry CSV File')
    argparser.add_argument('--csv', required=True, help='CSV file to load / update data to')
    return argparser.parse_args()

def main():
    args = parse_args()
    k8 = K8sManager()
    dkr = DockerManager()

    source_car = AssetRegistryManager()
    source_car.load_csv(args.csv)

    dest_car = AssetRegistryManager()
    deployments = k8.get_all_helm_deployments()

    for deployment in deployments:
        deployment_row = dict()
        deployment_row[AssetRegistryManager.NAMESPACE_KEY] = deployment.namespace
        deployment_row[AssetRegistryManager.ARTIFACT_KEY] = deployment.name
        deployment_row[AssetRegistryManager.VERSION_KEY] = deployment.version
        deployment_row[AssetRegistryManager.CHART_KEY] = deployment.chart
        pods = k8.find_chart_pods(deployment.name, deployment.namespace)
        if len(pods) == 0:
            pods = k8.find_chart_deployment_pods(deployment.name, deployment.namespace)

        if (len(pods) == 0):
            dest_car.set_asset(deployment_row)
            print(deployment_row)
        else:
            for pod in pods:
                containers = PodHelper.get_container_image_details(pod)
                if (len(containers) == 0):
                    dest_car.set_asset(deployment_row)
                    print(deployment_row)
                else:
                    for container in PodHelper.get_container_image_details(pod):
                        deployment_container_row = dict(deployment_row)
                        deployment_container_row[AssetRegistryManager.CONTAINER_NAME_KEY] = container.name
                        deployment_container_row[AssetRegistryManager.CONTAINER_IMAGE_KEY] = container.image
                        deployment_container_row[AssetRegistryManager.CONTAINER_IMAGE_ID_KEY] = container.digest

                        source_deployment_container_row = source_car.get_asset(deployment_container_row)

                        if (source_deployment_container_row != None) and (source_deployment_container_row.get(AssetRegistryManager.CONTAINER_IMAGE_ID_KEY) == container.digest):
                            deployment_container_row[AssetRegistryManager.CONTAINER_VERIFIED_KEY] = "Valid"
                        else:
                            print(f"Loading [{container.image}] image registry data")
                            registry_data = dkr.get_image_registry_data(container.image)
                            digest_valid = "Valid" if (registry_data is not None) and (registry_data.id == container.digest) else "Invalid"
                            deployment_container_row[AssetRegistryManager.CONTAINER_VERIFIED_KEY] = digest_valid

                        if (source_deployment_container_row != None) and (source_deployment_container_row.get(AssetRegistryManager.CONTAINER_UPDATED_KEY) is not None) and (len(source_deployment_container_row.get(AssetRegistryManager.CONTAINER_UPDATED_KEY)) > 0):
                            deployment_container_row[AssetRegistryManager.CONTAINER_UPDATED_KEY] = source_deployment_container_row[AssetRegistryManager.CONTAINER_UPDATED_KEY]
                        else:
                            print(f"Pulling [{container.image}] image")
                            img = dkr.pull_image(container.image)
                            created_date = None if img is None else img.attrs.get('Created')
                            deployment_container_row[AssetRegistryManager.CONTAINER_UPDATED_KEY] = '' if created_date is None else str(parser.parse(created_date).date())

                        dest_car.set_asset(deployment_container_row)
                        print(deployment_container_row)

    dest_car.save_csv(args.csv)

if __name__ == '__main__':
    main()
