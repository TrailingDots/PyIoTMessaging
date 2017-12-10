#!/usr/bin/env python
"""
    Designed for client router types and
    timing.

    The current hostname prefixes each message.
    line arguments to the logger.

    Usage:
        ./log_client_timing.py  count

    The arg "count" is a count of the number of
    logs to send for timing purposes.

    Omitting "count" results in a loop_count of 10000.

    The time gets reported after "count" logs
    have been sent.
"""
import sys
import platform
import timeit

import zmq

def send_msg(socket, msg):
    log = platform.node() + ' ' + msg
    socket.send(log)

# This port number MUST match the port number in
# logging_server_basic.py
PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.PUSH)

socket.connect('tcp://localhost:%s' % PORT)

loop_count = 10000  # Default loop count
if len(sys.argv) > 1:
    # User has requested a specfic loop count.
    loop_count = int(sys.argv[1])

def sender():
    send_msg(socket, 'Short message')

print('Timing loop for %d messages:' % loop_count)
print(timeit.timeit("sender()", setup="from __main__ import sender"))
