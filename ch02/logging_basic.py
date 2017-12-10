#!/usr/bin/env python

"""
    A very basic logger.

    Hard-coded socket assignments and filenames
    allow for a configuration-free implementation.

    Received logs don't get parsed or modified
    in any way, they just get written to the
    log file.

    Usage:
        ./logging_basic.py

    Terminate this program with Ctrl-C.
"""

import sys

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
    msg = socket.recv()
    log_file_handle.write(msg + '\n')
    log_file_handle.flush() # Insist on writing immediately
