# Chunker

## Overview

Chunker is a simple application that demonstrates how to configure and use a Portal in
chunking mode. In this mode, the underlying transport stack will use a chunking flow controller
to issue Interests for chunks of a supplied name. The flow controller will handle retries
and out of order reassembly of ContentObject responses.

## Basic Usage

stream_consumer.py and stream_producer.py are verbose, so run them in seperate windows.

1) Start the producer, telling it to provide 100 chunks of ~1200 bytes each for a name.
   > python stream_producer.py -l lci:/ccnx/stream -n 100 -s 1200

2) Start the consumer, asking for the same name you gave the producer.
  > python stream_consumer.py -l lci:/ccnx/stream

You should see a series of ContentObjects be received by the stream_consumer. Their payloads
are generated on the fly by the stream_producer and just consists of the chunk number (as
a string) repeated enough times to create a chunk of roughly the size specified.

## What's Missing?

TODO: @ALAN
