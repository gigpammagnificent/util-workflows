# list available receipes
@default:
    just --list
    
_asset_registry_init:
  #!/usr/bin/env bash
  if [ -d .venv ]; then
    source .venv/bin/activate
  else
    python3 -mvenv .venv --copies
    source .venv/bin/activate
  fi

  python3 -m pip install --upgrade pip
  pip3 install -r ./python/asset_registry/requirements.txt

asset-registry: _asset_registry_init
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/asset_registry/asset_registry/ --csv ./$(basename $PWD | sed 's/orch\-//g').csv


_apcrg_init:
  #!/usr/bin/env bash
  if [ -d .venv ]; then
    source .venv/bin/activate
  else
    python3 -mvenv .venv --copies
    source .venv/bin/activate
  fi

  python3 -m pip install --upgrade pip
  pip3 install -r ./python/apcrg/requirements.txt

apcrg-cp-dev-local *args: _apcrg_init
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/apcrg/apcrg/ \
    cp \
    --source-schema=https://apcrg.eks-dev01.gigndvr.com/apis/ccompat/v6 \
    --dest-schema=http://apcrg.localhost/apis/ccompat/v6 \
    {{args}}

apcrg-cp-dev-stage *args: _apcrg_init
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/apcrg/apcrg/ \
    cp \
    --source-schema=https://apcrg.eks-dev01.gigndvr.com/apis/ccompat/v6 \
    --dest-schema=http://apcrg.localhost/apis/ccompat/v6 \
    {{args}}
    

_ksqldb_deploy_init:
  #!/usr/bin/env bash
  if [ -d .venv ]; then
    source .venv/bin/activate
  else
    python3 -mvenv .venv --copies
    source .venv/bin/activate
  fi

  python3 -m pip install --upgrade pip
  pip3 install -r ./python/ksqldb_deploy/requirements.txt