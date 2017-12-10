#!/usr/bin/env python
import zmq
log_file_handle = open('./log.txt', 'wa')
context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://*:5555')
while True:
    msg = socket.recv()
    log_file_handle.write(msg + '\n')
    log_file_handle.flush()
