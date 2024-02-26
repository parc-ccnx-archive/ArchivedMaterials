#!/bin/bash
index=1;
numNodes=100;
while x=1;
do
    echo $index
    /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep CtlRSSI | awk -v div="$index" -v xval="$(echo $(( $RANDOM % 100 )))" -v yval="$(echo $(( $RANDOM % 100 )))" -v dt="$(date +%s%3)" ' { print div","xval","yval","$2 } ' >> $1;
    index=$(( (index + 1) % numNodes ))
    # sleep 0.5;
done
