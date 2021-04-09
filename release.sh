#!/usr/bin/env bash
set -euo pipefail

tox --recreate

rm -rf dist/
python setup.py sdist bdist_wheel
twine check dist/*

# TODO: automate releases on tag builds of travis
