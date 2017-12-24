#!/usr/bin/env python

def usage(exit_code):
    print(' '.join(sys.argv) + """\n
Testing utility to send log messages to the server.

This application simulates logs sent to
the logging server.

As a testing utility, this code has more
run-time options that might be expected.

The current hostname prefixes each message.

Usage:
    ./log_client.py [--port=port#]
            [--host=ahostname]
            [--log_msg=a_log_msg]
            [--sleep=0]
            [--count=number_msgs]

Where:
    --port=port#        - The port number for messaging.
                          Default: 5555
    --count=number_msgs - The # messages to send to log server.
                          Default: 10000
    --host=ahostname    - The name of the host where server lives.
                          Default: localhost
    --sleep=sec_sleep   - Seconds to sleep between messages.
    --svr-exit=true     - true to send exit msg to server at end
                          Default: false
    --log_msg=a_log_msg - The message to send to log server.
                          Default: 'A log message'
                          --log_msg=@EXIT@   causes the server to exit.
    """)
    sys.exit(exit_code)


import platform
import sys
import time

import zmq

# Sending this as a message causes the server to exit.
# The count also gets set to 1 after sending this message,
EXIT_SERVER = '@EXIT@'

def process_cmd_line(argv):
    """
    Command line code to handle user params
    """

    params = {
        # This port number MUST match the port number in
        # logging_basic.py
        'port': 5555,

        # Host name of log server
        # Change this to a remote name by supplying a --host option.
        'host': 'localhost',

        # Number of messages to send to log server
        'count': 10000,

        # The log message to send to log_server
        'log_msg': 'A log message',

        # True to send exit message to server at end
        'svr_exit': False,

        # Seconds to sleep between messages.
        # May be a floating point number like 0.5 for a half a sec
        'sleep': 0,

    }


    import getopt
    try:
        opts, _ = getopt.getopt(
                    argv, '',
                    ['port=',       # Port number.
                     'host=',       # hostname
                     'count=',      # Number of messages to send
                     'sleep=',      # Number of messages to send
                     'log_msg=',    # The log message to send to log server.
                     'log-msg=',    # The log message trivial alternative.
                     'svr-exit=',   # true to exit server at end
                     'svr_exit=',   # true to exit server at end
                     'help'         # Print help message then exit.
                     ])
    except getopt.GetoptError as err:
        print str(err)
        usage(1)

    for opt, arg in opts:
        if opt == '--help':
            usage(0)
        if opt == '--port':
            try:
                # PORT must be positive integer
                _ = int(arg)
            except Exception as err:
                print('Invalid port:%s' % str(err))
                usage(1)
            params['port'] = int(arg)   # Must convert to integer
        if opt == '--count':
            try:
                # count must be positive integer
                _ = int(arg)
            except Exception as err:
                print('Invalid message count:%s' % str(err))
                usage(1)
            params['count'] = int(arg)  # Must convert to integer
            continue
        if opt == '--sleep':
            try:
                # count must be positive integer
                _ = float(arg)
            except Exception as err:
                print('Invalid sleep value:%s' % str(err))
                usage(1)
            params['sleep'] = float(arg)  # Must convert to integer
            continue
        if opt in ['--log_msg', '--log-msg']:
            params['log_msg'] = arg
            continue
        if opt in ['--svr_exit', '--svr-exit']:
            params['svr_exit'] = True if 'true' == arg.lower() else False
            continue
        if opt == '--host':
            params['host'] = arg
            continue

    if params['log_msg'] == EXIT_SERVER:
        # Send one and only one message to the server.
        params['count'] = 1
    return params


def setup_zmq(your_host, port_number):
    """
    Setup environment for ZeroMQ message logging.

    your_host must be a string.
        your_host could be something like:
            "localhost" for logging on a local system.
            an IP address such as 192.168.1.76 .
            a remote system such as "trinity".
    The value of your_host depends on the location
    of log_server.

    port_number must be an integer.
        port_number is typically something like 5555, 5678, ...
        The port_number MUST batch the port number of the server!

    For testing purposes, use:
        setup_zmq('localhost', 5555)
    """
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect('tcp://%s:%d' % (your_host, port_number))
    return context, socket


def send_msg(socket, msg):
    """Send the message to the logger. Prefix the message with
    the host name of message origin."""
    log = platform.node() + ' ' + msg
    socket.send(log)


def mainline():
    """Top level logic for a client. Your clients will
    have different logic depending upon the application.

    This script targets sending logs to a log_server
    for testing purposes.
    """

    # If the user has entered command line options, process them
    params = process_cmd_line(sys.argv[1:])

    # Announce our run-time parameters
    print('%s --host=%s --port=%d --count=%d --svr_exit=%s --log_msg="%s"' %
            (sys.argv[0], params['host'], params['port'], params['count'],
                params['svr_exit'], params['log_msg']))

    # Create the ZeroMQ context and socket.
    context, socket = setup_zmq(params['host'], params['port'])

    log_msg = params['log_msg']
    sleep = params['sleep']
    # Send the requested number of messages to the server
    for ndx in xrange(params['count']):
        msg = '%d: %s' % (ndx, log_msg)
        send_msg(socket, msg)
        if sleep > 0:
            time.sleep()

    # Conditionally send the exit message to the server.
    if params['svr_exit']:
        send_msg(socket, EXIT_SERVER)

    print('Client exiting')
    sys.exit(0)

if __name__ == '__main__':
    mainline()

