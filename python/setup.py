import re
from setuptools import setup, find_packages

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('asset_registry/asset_registry.py').read(),
    re.M
    ).group(1)

setup(
    name="asset_registry",
    entry_points = {
        "console_scripts": ['asset_registry = asset_registry.asset_registry:main']
        },
    version=version,
    packages=find_packages(include=['asset_registry', 'asset_registry.*']),
    description="extract kubernetes release information into csv",
    install_requires=[
        'argparse==1.4.0'
        ,'dotmap==1.3.30'
        ,'kubernetes==21.7.0'
        ,'docker==5.0.3'
        ,'python-dateutil==2.8.2'
    ]
)