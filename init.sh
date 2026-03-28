#!/bin/bash

#
# init-rpi.sh
#
# Copyright (c) 2026 gcch
#

if [ "$(uname)" = "Linux" ]; then
	sudo apt install swig liblgpio-dev
fi

uv sync
