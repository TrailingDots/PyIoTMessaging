#!/usr/bin/env python

def usage(exit_code):
    print("""
        Received logs don't get parsed or modified
        in any way, they just get written to the
        log file.

        Usage:
            ./log_server.py [--log=aname] [--port=port#]

        Where:
            --log=aname   - The logfile name for output.
                            Default: ./log.txt
            --port=port#  - The port number for messaging.
                            Default: 5555

        Terminate this program with Ctrl-C.
    """)
    sys.exit(exit_code)

import sys
from datetime import datetime

import zmq

# Default logfile name
LOG_FILENAME = './log.txt'

# Use the default port
PORT = 5555

def process_cmd_line():
    """
    Command line code to handle user params
    """

    import getopt
    global LOG_FILENAME, PORT

    try:
        opts, _ = getopt.gnu_getopt(
                    sys.argv[1:], '',
                    ['port=',       # Port number.
                     'log=',        # Name of log file.
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
                # PORT must be integer
                _ = int(arg)
            except Exception as err:
                sys.stdout.write(str(err) + '\n')
                usage(1)
            PORT = int(arg) # Must convert to integer
            continue
        if opt == '--log':
            LOG_FILENAME = arg
            continue


def mainline():

    # If use has entered command line options, process them.
    process_cmd_line()

    # Open the log file for writing
    try:
        # Open log file. If problems, report and error out.
        log_file_handle = open(LOG_FILENAME, 'wa')
    except Exception as err:
        sys.stdout.write(str(err) + '\n')
        usage(1)

    # Establish a ZeroMQ Context and create a binding socket.
    context = zmq.Context()
    socket = context.socket(zmq.PULL)

    # Bind the socket to the port
    socket.bind('tcp://*:%s' % PORT)

    # Announce our run-time parameters
    print('log_server:log filename=%s, port=%d' % (LOG_FILENAME, PORT))

    while True:
        msg = socket.recv()
        if msg == '%EXIT%':
            print('Exiting')
            break
        msg_timestamp = '%s %s\n' % (str(datetime.now()), msg)
        log_file_handle.write(msg_timestamp)
        log_file_handle.flush() # Insist on writing immediately
    sys.exit(0)

if __name__ == '__main__':
    mainline()
