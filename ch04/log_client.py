#!/usr/bin/env python

def usage(exit_code):
    print("""
        Send logs to the logger for testing.
        This application simulates logs sent to
        the logging server.

        The current hostname prefixes each message.

        Usage:
            ./log_client_sender.py [--port=port#] 
                    [--host=ahostname]
                    [--log_msg=a_log_msg]
                    [--count=number_msgs]

        Where:
            --port=port#        - The port number for messaging.
                                  Default: 5555
            --count=number_msgs - The # messages to send to log server.
                                  Default: 10000
            --host=ahostname    - The name of the host where server lives.
                                  Default: localhost
            --svr-exit=true     - true to send exit msg to server at end
                                  Default: false
            --log_msg=a_log_msg - The message to send to log server.
                                  Default: 'A log message'
    """)
    sys.exit(exit_code)

import sys
import platform

import zmq

# This port number MUST match the port number in
# logging_basic.py
PORT = 5555

# Host name of log server
# Change this to a remote name by supplying a --host option.
HOSTNAME = 'localhost'

# Number of messages to send to log server
COUNT = 10000

# The log message to send to log_server
LOG_MSG = 'A log message'

# True to send exit message to server at end
SVR_EXIT = False

def send_msg(socket, msg):
    log = platform.node() + ' ' + msg
    socket.send(log)

def process_cmd_line():
    """
    Command line code to handle user params
    """

    import getopt
    global LOG_MSG, HOSTNAME, PORT, COUNT, SVR_EXIT

    try:
        opts, _ = getopt.gnu_getopt(
                    sys.argv[1:], '',
                    ['port=',       # Port number.
                     'host=',       # hostname
                     'count=',      # Number of messages to send
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
                sys.stdout.write(str(err) + '\n')
                usage(1)
            PORT = int(arg) # Must convert to integer
        if opt == '--count':
            try:
                # COUNT must be positive integer
                _ = int(arg)
            except Exception as err:
                sys.stdout.write(str(err) + '\n')
                usage(1)
            COUNT = int(arg) # Must convert to integer
            continue
        # Notice that a common type gets handled.
        if opt in ['--log_msg', '--log-msg']:
            LOG_MSG = arg
            continue
        if opt in ['--svr_exit', '--svr-exit']:
            SVR_EXIT = True if arg == arg.lower() else False
            continue
        if opt == '--host':
            HOSTNAME = arg
            continue


def mainline():
    # If the user has entered command line options, proces them
    process_cmd_line()

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)

    socket.connect('tcp://%s:%d' % (HOSTNAME, PORT))

    # Announce our run-time parameters
    print('log_client:hostname=%s, port=%d, count=%d, svr_exit=%s, msg="%s"' % \
            (HOSTNAME, PORT, COUNT, SVR_EXIT, LOG_MSG))

    for ndx in xrange(COUNT):
        msg = '%d: %s' % (ndx, LOG_MSG)
        send_msg(socket, msg)

    # Send the exit message to the server
    # No frills such as timestamp, host, etc. added!
    if SVR_EXIT:
        socket.send('%EXIT%')

    sys.exit(0)

if __name__ == '__main__':
    mainline()

