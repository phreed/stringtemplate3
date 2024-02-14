#!/bin/bash

CL=$(head -n 1 changelists)

echo -n "Are you sure you have completed CL $CL? "
read ANSWER
if [ "$ANSWER" = "y" ]; then
    echo >>changelists.done $CL
    tail -n +2 changelists >changelists.tmp
    mv -f changelists.tmp changelists
else
    echo "Aborted."
    exit 1
fi



