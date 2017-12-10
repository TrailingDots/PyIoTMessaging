#!/usr/bin/env python

"""
    Basic utility to send logs to the logger.
    This application simply passes on the command
    The current hostname prefixes each message.
    line arguments to the logger.

    Usage:
        ./log_cmd_basic.py  arg1 arg2 arg3

    The above command results in "arg1 arg2 arg3"
    written in the log file with logging_basic.py
"""

import sys
import platform

import zmq

def send_msg(socket, msg):
    log = platform.node() + ' ' + msg
    socket.send(log)

# This port number MUST match the port number in
# logging_basic.py
PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.PUSH)

socket.connect('tcp://localhost:%s' % PORT)

send_msg(socket, ' '.join(sys.argv[1: len(sys.argv)]))
send_msg(socket, 'A test message to prove send_msg() gets called.')

