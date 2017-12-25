#!/usr/bin/env python
def usage():
    print(' '.join(sys.argv) + """\n
Received logs have the current time prepended
to the message.
Otherwise logs don't get parsed or modified
in any way, they just get written to the
log file.

Usage:
    ./log_server.py [--log=aname] [--port=port#]
        [--log-append=true/false] [--echo=true/false]

Where:
    --log=aname   - The log filename for output.
                    Default: ./log.log
    --log_append=true/false   - Append to existing log?
                    Also: --log-append=... as an alias
                    Default: true
    --port=port#  - The port number for messaging.
                    Default: 5555
    --echo=true/false - true to echo to stdout, 
                    false means keep silent
                    Default: false meaning no echo

Terminate this program with Ctrl-C
or:
    Send a log message with @EXIT@ as the message.
    """)

import sys
from datetime import datetime

import zmq

# Sending this as a message causes the server to exit.
# The count also gets set to 1 after sending this message,
EXIT_SERVER = '@EXIT@'

# Echo logs to the console?
# If True, all logs get echo to the console.
# If False, logging proceeds with no console echo.
# This switch may be set with a message for convenience.
#
# To use in a message, send '@ECHO=true' or
# '@ECHO=false' to log_server. The message may 
# be in either upper or lower case.
ECHO_SERVER_FALSE = '@ECHO=false@'
ECHO_SERVER_TRUE = '@ECHO=true@'

# Logic switch after processing the ECHO_SERVER
# message.
ECHO_SWITCH = False

def echo_message_detector(msg):
    """Given msg as the current received message,
    parse it. If the message contains
    ECHO_SERVER_TRUE or FALSE, set ECHO_SWITCH
    appropriately.

    Always return the current state of ECHO_SWITCH.
    """
    global ECHO_SWITCH
    if ECHO_SERVER_FALSE in msg:
        ECHO_SWITCH = False
    if ECHO_SERVER_TRUE in msg:
        ECHO_SWITCH = True
    return ECHO_SWITCH


def dict_to_cmd_string(params):
    """Utility to format run-time parameters as if
    they came from the command line.
    
    Input: The params as created by process_cmd_line.
    Output: Formatted string of run-time switches."""

    out = ""
    for key, value in params.items():
        out = out + ('%s=%s ' % (key, value))
    return out


def process_cmd_line(argv):
    """
    Command line code to handle user params
    """
    global ECHO_SWITCH

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
                argv, '',
                    ['port=',       # Port number.
                     'log=',        # Name of log file.
                     'echo=',       # Echo logs to console
                     'log-append=', # Append to existing log or not?
                     'log_append=', # Append to existing log or not?
                     'help'         # Print help message then exit.
                     ])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt == '--help':
            usage()
            sys.exit(0)
        if opt == '--port':
            try:
                # port must be integer
                _ = int(arg)
            except ValueError as err:
                print('Invalid port number:%s' % err)
                usage()
                sys.exit(1)
            params['port'] = int(arg) # Must convert to integer
            continue
        if opt in ['--log-append', '--log_append']:
            params['log_append'] = True if arg.lower() == 'true' else False
            continue
        if opt in ['--echo']:
            params['echo'] = True if arg.lower() == 'true' else False
            continue
        if opt == '--log':
            params['log_filename'] = arg
            continue

    # Set ECHO_SWITCH to the optional setting.
    ECHO_SWITCH = params['echo']

    # Announce our run-time parameters
    print('%s %s' %
            (sys.argv[0], dict_to_cmd_string(params)))
    return params


def open_log_file_for_writing(params):
    # Open the log file for writing
    try:
        # Open log file with append. If problems, report and error out.
        # Depending upon runtime options, append to existing log
        # or wipe existing log, if any.
        wipe_or_append = 'a' if params['log_append'] else 'wa'
        log_file_handle = open(params['log_filename'], wipe_or_append)
    except Exception as err:
        # Due to the nature of this logic, this should never happen.
        print('Invalid file open parameter:%s' % str(err))
        usage()
        sys.exit(1)
    return log_file_handle

def mainline():

    # If use has entered command line options, process them.
    params = process_cmd_line(sys.argv[1:])

    log_file_handle = open_log_file_for_writing(params)

    # Establish a ZeroMQ Context and create a binding socket.
    context = zmq.Context()
    socket = context.socket(zmq.PULL)

    # Bind the socket to the port
    socket.bind('tcp://*:%d' % params['port'])

    while True:
        msg = socket.recv()
        msg_timestamp = '%s %s\n' % (str(datetime.now()), msg)
        #import pdb; pdb.set_trace()
        if echo_message_detector(msg):
            sys.stdout.write(msg_timestamp)
        if EXIT_SERVER in msg:
            print('server Exiting')
            break
        log_file_handle.write(msg_timestamp)
        # Comment out for production code. This slows the server down.
        log_file_handle.flush() # Insist on writing immediately
    sys.exit(0)


if __name__ == '__main__':
    mainline()
