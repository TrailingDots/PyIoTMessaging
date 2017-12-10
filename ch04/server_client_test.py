#!/usr/bin/env python
#
# Test suite for log_server.py and log_client.py
#

from unittest import TestCase, main
import os
import subprocess        # To spawn subprocesses
import time

from listening_port import listening, is_listening
import log_client 
import log_server

LOG_SERVER_NAME = './log_server.py'
LOG_CLIENT_NAME = './log_client.py'

def create_process(cmd_line):
    print('create_process:%r' % cmd_line)
    proc = subprocess.Popen(cmd_line, shell=True)
    return proc


def load_file(filename):
    """Read a file into memory and return that file."""
    if not os.path.isfile(filename):
        return None
    with open(filename, 'r') as content_file:
        content = content_file.read()
    return content

def count_lines_in_file(filename):
    wc_out, wc_err = subprocess.Popen('/usr/bin/wc -l %s' % filename,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT).communicate()
    
    print('wc_out:%s' % wc_out)
    wc_count = int(wc_out.split(' ')[0])
    return wc_count

if __name__ == '__main__':

    log_name = 'abc.txt'
    count = 10
    port = 5555

    #============================================================
    # Determine if this port has been assigned
    # If any procss are listening, attempt to kill them.
    #============================================================
    port_status = listening(port, kill=True)
    if not port_status == 0:
        print('For port %s, listeners:%d' % (port, port_status))
        port_status = is_listening(port)
        if not port_status == 0:
            print('port %d: Attempted to kill, but %d listeners remain' % \
                    (port, port_status))

    #============================================================
    # Create a server
    #============================================================
    server_proc = create_process('%s --log=%s --port=%d' % 
        (LOG_SERVER_NAME, log_name, port))

    #============================================================
    # Create a client and send 10 logs
    #============================================================
    client_proc= create_process('%s --svr-exit=true --count=%d --port=%d' %
        (LOG_CLIENT_NAME, count, port))


    #============================================================
    # look at the client output
    #============================================================
    client_out, client_err = client_proc.communicate()
    print('after comm: client_out:%s\nclient_err:%s' % \
            (client_out, client_err))

    svr_status = server_proc.poll()
    print('svr_status=%r' % svr_status)

    clt_status = client_proc.poll()
    print('clt_status=%r' % clt_status)

    server_out, server_err = server_proc.communicate()
    print('after comm: stdout:%s\nstderr:%s' % \
            (server_out, server_err))

    data = load_file(log_name)
    print('data:%s' % data)

    #============================================================
    # Log file must have 'count' lines.
    #============================================================
    wc_lines = count_lines_in_file(log_name)
    
    if not wc_lines == count:
        print('ERROR: Expected %d lines, got %d lines' % \
                (count, wc_lines))

