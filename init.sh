#!/bin/bash

#
# init-rpi.sh
#
# Copyright (c) 2026 gcch
#

if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
	sudo apt install swig liblgpio-dev
fi

if [ "$(uname)" == "Debian" ]; then
	i2c-tools
fi

uv sync
