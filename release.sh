#!/usr/bin/env bash
set -euo pipefail

tox --recreate

rm -rf dist/
poetry build

# TODO: automate releases on tag builds of travis
