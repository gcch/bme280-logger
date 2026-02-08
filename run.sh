#!/bin/bash

i2cdetect -y 1

SCRIPT_DIR=$(cd $(dirname $0); pwd)
cd "${SCRIPT_DIR}"
$HOME/.local/bin/uv run "${SCRIPT_DIR}/main.py"
