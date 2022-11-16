from dotmap import DotMap
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.rest import ApiException
from kubernetes.client.models.v1_pod import V1Pod
from kubernetes.client.models.v1_deployment import V1Deployment
from kubernetes.client.models.v1_component_status import V1ComponentStatus
from kubernetes.client.models.v1_component_status_list import V1ComponentStatusList
from typing import List

class K8sManager:

    def __init__(self) -> None:
        super().__init__()
        config.load_kube_config()
        try:
            c = Configuration().get_default_copy()
        except AttributeError:
            c = Configuration()
            c.assert_hostname = False
        Configuration.set_default(c)
        self._core_v1 = client.CoreV1Api()
        self._apps_v1 = client.AppsV1Api()
        self._batch_v1 = client.BatchV1Api()


    def find_chart_deployments(self, release_name: str, namespace: str) -> List[V1Deployment]:
        kubernetes_deployments = [
            self._apps_v1.list_namespaced_deployment(namespace, label_selector='app.kubernetes.io/name={}'.format(release_name)),
            self._apps_v1.list_namespaced_deployment(namespace, label_selector='app.kubernetes.io/instance={}'.format(release_name)),
            self._apps_v1.list_namespaced_deployment(namespace, label_selector='release={}'.format(release_name)),
            self._apps_v1.list_namespaced_deployment(namespace, label_selector='app={}'.format(release_name))
        ]
        deployments = dict()

        for deploymentlist in kubernetes_deployments:
            for deployment in deploymentlist.items:
                deployments[f"{deployment.metadata.namespace}-{deployment.metadata.name}"] = deployment

        return list(deployments.values())

    def find_chart_pods(self, release_name: str, namespace: str) -> List[V1Pod]:
        kubernetes_pods = [
            self._core_v1.list_namespaced_pod(namespace, label_selector='app.kubernetes.io/name={}'.format(release_name)),
            self._core_v1.list_namespaced_pod(namespace, label_selector='app.kubernetes.io/instance={}'.format(release_name)),
            self._core_v1.list_namespaced_pod(namespace, label_selector='release={}'.format(release_name)),
            self._core_v1.list_namespaced_pod(namespace, label_selector='app={}'.format(release_name))
        ]
        pods = dict()

        for podlist in kubernetes_pods:
            for pod in podlist.items:
                pods[f"{pod.metadata.namespace}-{pod.metadata.name}"] = pod

        return list(pods.values())

    def find_chart_deployment_pods(self, release_name: str, namespace: str) -> List[V1Pod]:
        pods = dict()

        deployments = self.find_chart_deployments(release_name, namespace)
        for deployment in deployments:
            labels = ""
            for selectorlabel, selectorvalue in deployment.spec.selector.match_labels.items():
                if (len(labels)>0):
                    labels += ","
                labels += f"{selectorlabel}={selectorvalue}"
            deployment_pods = self._core_v1.list_namespaced_pod(namespace, label_selector=labels),

            for podlist in deployment_pods:
                for pod in podlist.items:
                    pods[f"{pod.metadata.namespace}-{pod.metadata.name}"] = pod

        return list(pods.values())

    def get_all_helm_deployments(self):
        helm_label_selector = 'app.kubernetes.io/managed-by=Helm'
        helm_deployments = dict()

        kubernetes_resources = [
            self._apps_v1.list_deployment_for_all_namespaces(label_selector=helm_label_selector),
            self._apps_v1.list_stateful_set_for_all_namespaces(label_selector=helm_label_selector),
            self._core_v1.list_service_for_all_namespaces(label_selector=helm_label_selector),
            self._core_v1.list_config_map_for_all_namespaces(label_selector=helm_label_selector),
            self._core_v1.list_secret_for_all_namespaces(label_selector=helm_label_selector),
            self._batch_v1.list_cron_job_for_all_namespaces(label_selector=helm_label_selector),
            self._batch_v1.list_job_for_all_namespaces(label_selector=helm_label_selector)
        ]

        for resourcelist in kubernetes_resources:
            for resource in resourcelist.items:
                chart = resource.metadata.labels.get('chart') or resource.metadata.labels.get('helm.sh/chart')
                release = resource.metadata.annotations.get('meta.helm.sh/release-name')
                instance = resource.metadata.labels.get('app.kubernetes.io/instance')
                version = resource.metadata.labels.get('app.kubernetes.io/version')
                revision = resource.metadata.annotations.get('deployment.kubernetes.io/revision')
                namespace = resource.metadata.namespace

                deployment = DotMap({
                        "name": instance or release or None,
                        "chart": chart or None,
                        "version": version or None,
                        "namespace": namespace or None,
                        "revision": revision or None
                    })

                key = f"{deployment['namespace']}-{deployment['name']}"
                cached_deployment = helm_deployments.get(key)

                if cached_deployment == None:
                    helm_deployments[key] = deployment
                else:
                    for key, value in cached_deployment.items():
                        if (cached_deployment[key] == None) and (deployment[key] != None):
                            cached_deployment[key] = deployment[key]

        return list(helm_deployments.values())
