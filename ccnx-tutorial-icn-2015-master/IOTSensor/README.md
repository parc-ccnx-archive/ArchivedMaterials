# IOTSenser

## Overview

The IOTSensor application is a highly trivial CCNx 1.0 application that will
send a value to a given collector with a well-defined name. The sensor application
will receive some acknowledgement or computed value from the collector in response.
This application exists to illustrate the basic Interest and Content Object
exchange mechanics in Python.

## Basic Usage

> python iot_sensor.py -l lci:/tutorial/iot/collector/info 1234

## What's Missing?

Implement the main body of the IoT sensor application, which (1) creates and
Interest, (2) sends it to the server using the CCNx Portal, (3) receives the
Content Object response, and (4) prints the result.

## Message Syntax

Interest:
    lci:/tutorial/iot/collector/info
Content Object:
    lci:/tutorial/iot/collector/info
    "Something fun..."

Interest:
    lci:/tutorial/iot/collector/value
Content Object:
    lci:/tutorial/iot/collector/value
    "OK"

## Extensions:

Possible extensions include:

- Integrate a key-exchange algorithm into the sensor to encrypt all values
sent to the collector.
- Implement Interest signing.
