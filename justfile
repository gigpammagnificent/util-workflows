# list available receipes
@default:
    just --list
    
_pyinit:
  #!/usr/bin/env bash
  if [ -d .venv ]; then
    source .venv/bin/activate
  else
    python3 -mvenv .venv --copies
    source .venv/bin/activate
  fi

  python3 -m pip install --upgrade pip
  pip3 install -r ./python/asset_registry/requirements.txt

asset-registry: _pyinit
  #!/usr/bin/env bash
  source .venv/bin/activate
  python3 ./python/asset_registry/ --csv ./$(basename $PWD | sed 's/orch\-//g').csv

