#!/usr/bin/env python

"""
    Basic utility to send logs to the logger.
    This application simply passes on the command
    line arguments to the logger.

    Usage:
        ./log_cmd_basic.py  arg1 arg2 arg3

    The above command results in "arg1 arg2 arg3"
    written in the log file with logging_basic.py
"""

import sys

import zmq

# This port number MUST match the port number in
# logging_basic.py
PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.PUSH)

socket.connect('tcp://localhost:%s' % PORT)

log = ' '.join(sys.argv[1: len(sys.argv)])
socket.send(log)

