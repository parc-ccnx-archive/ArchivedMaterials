#!/bin/bash
while x=1;
do
    /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep CtlRSSI | awk -v dt="$(date +%s%3)" ' { print dt","  $2 } ' >> $1; sleep 0.5;
done
