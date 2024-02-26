# Gateway

## Overview

The Gateway application is a simple CCNx-to-HTTP gateway for requesting IP-based
web content via CCNx names. Interest names have a natural correspondence to HTTP
GET requests, as shown below:

TODO: SCHEMA

Currently, only a HTTP gateway is implemented.

## Basic Usage

Starting the gateway:
> python gateway.py lci:/gateway/prefix

Sample queries:
> python query.py lci:/gateway/www.parc.com
> python query.py lci:/gateway/www.ucla.edu
> python query.py lci:/gateway/www.ucsc.edu

## What's Missing?

Implement the Interest-to-HTTP request parsing logic using Interest name components.

## Extensions:

Possible extensions include:

- Implement a CCNx-to-Y gateway for the following protocols: FTP, TCP, DNS, IMAP, SSH/TLS.
- Add state to each gateway connection.
