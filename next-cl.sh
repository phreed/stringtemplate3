#!/bin/bash

CL=$(head -n 1 changelists)

python2.5 -m webbrowser -t "http://fisheye2.cenqua.com/changelog/stringtemplate?cs=$CL"

p4 describe $CL


