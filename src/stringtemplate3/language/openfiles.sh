#!/bin/bash

while [ $# -gt 0 ]; do
    if [ -e "$1" -a ! -w "$1" ]; then
	p4 edit "$1"
    fi
    shift
done
