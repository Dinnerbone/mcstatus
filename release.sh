#!/usr/bin/env bash
set -euo pipefail

[ ! -d venv ] && (
  python3 -m virtualenv venv
  source venv/bin/activate
  pip install -r test-requirements.txt
  pip check
)
source venv/bin/activate

python -m nose

rm -rf dist/
python setup.py sdist bdist_wheel
twine check dist/*

# TODO: automate releases on tag builds of travis
