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


_apicurio_copy_init:
  #!/usr/bin/env bash
  if [ -d .venv ]; then
    source .venv/bin/activate
  else
    python3 -mvenv .venv --copies
    source .venv/bin/activate
  fi

  python3 -m pip install --upgrade pip
  pip3 install -r ./python/apicurio_copy/requirements.txt

apicurio_copy-dev-local *args: _apicurio_copy_init
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/apicurio_copy/apicurio_copy/ \
    --source-schema=https://apcrg.eks-dev01.gigndvr.com/apis/ccompat/v6 \
    --dest-schema=http://apcrg.localhost/apis/ccompat/v6 \
    {{args}}

apicurio_copy-dev-stage *args: _apicurio_copy_init
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/apicurio_copy/apicurio_copy/ \
    --source-schema=https://apcrg.eks-dev01.gigndvr.com/apis/ccompat/v6 \
    --dest-schema=http://apcrg.localhost/apis/ccompat/v6 \
    {{args}}
    