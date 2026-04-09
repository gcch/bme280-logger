#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $0); pwd)
cd "${SCRIPT_DIR}"

if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    i2cdetect -y 1
    ${SCRIPT_DIR}/.venv/bin/python3 "${SCRIPT_DIR}/main-i2c.py"
else
    ${SCRIPT_DIR}/.venv/bin/python3 "${SCRIPT_DIR}/main-ftdi.py"
fi
