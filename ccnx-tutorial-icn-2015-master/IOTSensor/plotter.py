#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Christopher A. Wood, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import datetime
import time
import plotly
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *
import tailer
import sys
import numpy as np

sys.path.append("../")
from CCNxClient import *

keyfile = open("plotly.key", "r")
lines = keyfile.readlines()
lines = map(lambda x : x.strip(), lines)

py.sign_in(lines[0], lines[1])
tls.set_credentials_file(stream_ids=lines[2:])

stream_ids = tls.get_credentials_file()['stream_ids']
stream_id = stream_ids[0]

stream = Stream(token=stream_id, maxpoints=80)

dataTrace = Scatter(x=[], y=[], mode='lines+markers', stream=stream)

data = Data([dataTrace])
layout = Layout(title='Time Series')

fig = Figure(data=data, layout=layout)
unique_url = py.plot(fig, filename='CCNxIOT-Collector')

s = py.Stream(stream_id)
s.open()

client = CCNxClient()
client.listen("lci:/tutorial/iot/collector")
while True:
    try:
        name, data = client.receive()
        print name, data
        y = int(name.split("/")[-1])
        x = datetime.datetime.now()
        s.write(dict(x=x, y=y))
        print "writing %s" % (str(dict(x = x, y = y)))
        client.reply(name, "OK")
    except:
        pass
s.close()
