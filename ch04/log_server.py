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
                            Default: ./log.log
            --log_append=true/false   - Append to existing log?
                            Defautl: true
            --port=port#  - The port number for messaging.
                            Default: 5555
            --echo=true/false - true to echo to stdout, false=keep silent
                            Default: false meaning no echo

        Terminate this program with Ctrl-C
        or:
            Send a log message with #EXIT# in it.
            Sending the log msg #EXIT# will cause a PUB msg
            with #EXIT# as the message contents.
    """)
    sys.exit(exit_code)

import sys
from datetime import datetime

import zmq


def process_cmd_line():
    """
    Command line code to handle user params
    """

    # Parameters from command line default values.
    params = {
        # Default logfile name
        'log_filename': './log.log',

        # Append to existing logs or not?
        'log_append': True,

        # Use the default port
        'port': 5555,

        # True to echo msg to stdout
        'echo': False
    }

    import getopt
    try:
        opts, _ = getopt.gnu_getopt(
                    sys.argv[1:], '',
                    ['port=',       # Port number.
                     'log=',        # Name of log file.
                     'log-append=', # Append to existing log or not?
                     'log_append=', # Append to existing log or not?
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
                # port must be integer
                _ = int(arg)
            except Exception as err:
                sys.stdout.write(str(err) + '\n')
                usage(1)
            params['port'] = int(arg) # Must convert to integer
            continue
        if opt in ['--log-append', '--log_append']:
            params['log_append'] = True if arg.lower() == 'true' else False
            continue
        if opt == '--log':
            params['log_filename'] = arg
            continue
    return params

def mainline():

    # If use has entered command line options, process them.
    params = process_cmd_line()

    # Open the log file for writing
    try:
        # Open log file with append. If problems, report and error out.
        # Depending upon runtime options, append to existing log
        # or wipe existing log, if any.
        wipe_or_append = 'a' if params['log_append'] else 'wa'
        log_file_handle = open(params['log_filename'], wipe_or_append)
    except Exception as err:
        sys.stdout.write(str(err) + '\n')
        usage(1)

    # Establish a ZeroMQ Context and create a binding socket.
    context = zmq.Context()
    socket = context.socket(zmq.PULL)

    # Bind the socket to the port
    socket.bind('tcp://*:%d' % params['port'])

    # Announce our run-time parameters
    print('log_server:log filename=%s, port=%d' % (params['log_filename'], params['port']))

    while True:
        msg = socket.recv()
        if '#EXIT#' in msg:
            print('server Exiting')
            break
        msg_timestamp = '%s %s\n' % (str(datetime.now()), msg)
        log_file_handle.write(msg_timestamp)
        log_file_handle.flush() # Insist on writing immediately
    sys.exit(0)


if __name__ == '__main__':
    mainline()
