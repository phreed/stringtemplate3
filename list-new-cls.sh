#!/bin/bash

LASTCL=$(($(tail -n 1 changelists.done) + 1))

p4 changes \
    //depot/code/stringtemplate/java/...@$LASTCL,#head \
  | cut -f 2 -d ' ' | sort -n | uniq | tee changelists
