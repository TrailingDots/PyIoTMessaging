#!/usr/bin/env python
"""
    A very basic logger to investigate timings
    and socket typed.

    Usage:
        ./logging_server_timing.py

    Terminate this program with Ctrl-C.
"""

import sys
from datetime import datetime

import zmq

# Change this to something you like!
LOG_FILENAME = './log.txt'

# Open the log file for writing
log_file_handle = open(LOG_FILENAME, 'wa')

# Use the default port
PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.PULL)

# Bind the socket to the port
socket.bind('tcp://*:%s' % PORT)

while True:
    # Discard envelop
    socket.recv()
    msg = socket.recv()
    msg_timestamp = '%s %s\n' % (str(datetime.now()), msg)
    #log_file_handle.write(msg_timestamp)
    #log_file_handle.flush() # Insist on writing immediately

