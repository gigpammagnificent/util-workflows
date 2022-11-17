import csv

class AssetRegistryManager:
    NAMESPACE_KEY='namespace'
    ARTIFACT_KEY='artifact'
    VERSION_KEY='version'
    CHART_KEY='chart'
    CONTAINER_NAME_KEY='container'
    CONTAINER_IMAGE_KEY='image'
    CONTAINER_IMAGE_ID_KEY='digest'
    CONTAINER_VERIFIED_KEY='digest_verified'
    CONTAINER_UPDATED_KEY='updated'

    def __init__(self) -> None:
        super().__init__()
        self._assets = dict()

    def get_asset_fingerprint(self, asset: dict) -> str:
        return f"{asset.get(AssetRegistryManager.NAMESPACE_KEY) or ''}-{asset.get(AssetRegistryManager.ARTIFACT_KEY) or ''}-{asset.get(AssetRegistryManager.VERSION_KEY) or ''}-{asset.get(AssetRegistryManager.CONTAINER_NAME_KEY) or ''}"

    def load_csv(self, file_path: str) -> None:
        self._assets = dict()
        try:
            with open(file_path, 'r') as file:
                csvreader = csv.reader(file)
                csv_header = next(csvreader)
                for row in csvreader:
                    asset = dict()
                    for i in range(len(csv_header)):
                        key = csv_header[i]
                        value = None if i>=len(row) else row[i]
                        asset[key] = value
                    self._assets[self.get_asset_fingerprint(asset)] = asset
        except:
            pass

    def save_csv(self, file_path: str) -> None:
        csv_header = [AssetRegistryManager.NAMESPACE_KEY,
                         AssetRegistryManager.ARTIFACT_KEY,
                         AssetRegistryManager.VERSION_KEY,
                         AssetRegistryManager.CHART_KEY,
                         AssetRegistryManager.CONTAINER_NAME_KEY,
                         AssetRegistryManager.CONTAINER_UPDATED_KEY,
                         AssetRegistryManager.CONTAINER_IMAGE_KEY,
                         AssetRegistryManager.CONTAINER_IMAGE_ID_KEY,
                         AssetRegistryManager.CONTAINER_VERIFIED_KEY]

        csv_rows = list(self._assets.values())
        csv_rows.sort(key = lambda x: self.get_asset_fingerprint(x))

        with open(file_path, 'w', encoding='UTF8') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(csv_header)

            for asset in csv_rows:
                row = []
                for i in range(len(csv_header)):
                    header = csv_header[i]
                    row.append(asset.get(header) or '')
                csv_writer.writerow(row)

    def get_asset(self, fingerprint: str or dict) -> dict or None:
        if type(fingerprint) == dict:
            return self._assets.get(self.get_asset_fingerprint(fingerprint))
        else:
            return self._assets.get(fingerprint)

    def set_asset(self, asset: dict) -> None:
        self._assets[self.get_asset_fingerprint(asset)] = asset
