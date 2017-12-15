#!/usr/bin/env python
#
# Test suite for log_server.py and log_client.py
#

import datetime         # for timing
import functools
import os
import sys
import subprocess       # To spawn subprocesses
import time
from unittest import TestCase, main

from listening_port import listening, is_listening
import log_client 
import log_server

LOG_SERVER_NAME = './log_server.py'
LOG_CLIENT_NAME = './log_client.py'


def tracer(fn):
    """
    Decorator to track testing methods through the logger.
    """
    from itertools import chain
    def wrapped(*v, **k):
        name = fn.__name__
        print '\n\n----> %s(%s)' % (
            name, ','.join(map(repr, chain(v, k.values()))))
        return fn(*v, **k)
    return wrapped


def accum_sleep_time(sleep_time):
    """Accumulate the total sleep time. The server does not
    know the queue size so the delay in sleep allows the
    server to catch up with queue values. YUCK! I HATE
    forced delays.
    """
    time.sleep(sleep_time)


def stop_timer(start, sleeper):
    """Given a start time and the sleep time,
    return the delta suitable for printing via %s"""
    stop = datetime.datetime.now()
    delta = stop - (start + datetime.timedelta(0, sleeper))
    return delta


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

def kill_listening_processes(port):
    """
    Determine if this port has been assigned
    If any procss are listening, attempt to kill them.
    Answers # listeners.
    If 0 listeners, then proceed.
    If non-0, then the test should not proceed.
    """
    port_status = listening(port, kill=True)
    if not port_status == 0:
        print('For port %s, listeners:%d' % (port, port_status))
        port_status = is_listening(port)
        if not port_status == 0:
            print('port %d: Attempted to kill, but %d listeners remain' % \
                    (port, port_status))
            return port_status
    return 0    # No listeners


def report_client_server_stdout(client_proc, server_proc):
    client_out, client_err = client_proc.communicate()
    print('after comm: client_out:%s\nclient_err:%s' % \
            (client_out, client_err))

    svr_status = server_proc.poll()
    print('svr_status=%r' % svr_status)

    # Look at the server output
    clt_status = client_proc.poll()
    print('clt_status=%r' % clt_status)

    server_out, server_err = server_proc.communicate()
    print('after comm: stdout:%s\nstderr:%s' % \
            (server_out, server_err))


def get_line_count(log_name):
    # Anwer the actual_line_count

    # Count the lines of output
    data = load_file(log_name)
    #print('data:%s' % data)    # Echo data to stdout

    #============================================================
    # Log file must have 'count' lines.
    # This could be better - could use regex to determine
    # if the logged data meets expectations.
    #============================================================
    return  count_lines_in_file(log_name)


class ServerClientTest(TestCase):

    log_name = 'abc.txt'
    count = 10
    noisy = True
    port = 5555

    def setUp(self):
        # Kill any listening processes.
        kill_listening_processes(ServerClientTest.port)
        # Remove log file if it exists.
        if os.path.isfile(ServerClientTest.log_name):
            os.remove(ServerClientTest.log_name)

    @tracer
    def test_happy_path(self):
        count = 10000   # 10K logs from client to server
        # Create a server
        server_proc = create_process('%s --log=%s --port=%d' % 
            (LOG_SERVER_NAME, ServerClientTest.log_name, ServerClientTest.port))

        # Create a client and send logs
        client_proc= create_process('%s --svr-exit=true --count=%d --port=%d' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))

        # Look at the client and server output
        if ServerClientTest.noisy:
            report_client_server_stdout(client_proc, server_proc)

        self.assertEqual(count, get_line_count(ServerClientTest.log_name))


    @tracer
    def test_two_clients(self):
        count = 10000   # 10k logs
        sleeper = 1
        # Create a server
        server_proc = create_process('%s --log=%s --port=%d' % 
            (LOG_SERVER_NAME, ServerClientTest.log_name, ServerClientTest.port))

        # Create a client and send 10 logs
        client_proc1 = create_process('%s --count=%d --port=%d --log_msg=Client1' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))

        # Create another client and send 20 logs
        client_proc2 = create_process('%s --count=%d --port=%d --log_msg=Client2' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))

        # Wait for the 2 clients to terminate
        client_proc1.communicate()
        client_proc2.communicate()

        accum_sleep_time(sleeper)

        # Create another client simply to exit
        client_exit = create_process('%s --svr-exit=true --count=1 --port=%d --log_msg=#EXIT#' %
            (LOG_CLIENT_NAME, ServerClientTest.port))

        # Look at the client and server output
        if ServerClientTest.noisy:
            report_client_server_stdout(client_proc1, server_proc)
            report_client_server_stdout(client_proc2, server_proc)

        self.assertEqual(2*count, get_line_count(ServerClientTest.log_name))

    @tracer
    def test_timing_100k(self):
        """Time sending 10000 simple logs."""
        log_count = 100000    # Number of l0gs to send.
        log_name = '100k.log'
        # Create a server
        server_proc = create_process('%s --log=%s --port=%d' % 
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        # Create a client and send 10 logs
        client_proc1 = create_process('%s --svr_exit=true --count=%d --port=%d --log_msg="100k logs"' %
            (LOG_CLIENT_NAME, log_count, ServerClientTest.port))

        # Create another client simply to exit
        start = datetime.datetime.now()

        # Look at the client and server output
        if ServerClientTest.noisy:
            report_client_server_stdout(client_proc1, server_proc)

        stop = datetime.datetime.now()
        delta = stop - start    # Duration to send the logs
        print('Time to send %d logs:%s' % (log_count, delta))

        self.assertEqual( log_count, get_line_count(log_name) )


    @tracer
    def test_timing_10k_20clients(self):
        """Time sending 1000 logs in each of 20 clients."""

        log_count = 10000    # Number of l0gs to send.
        log_name = '20client.log'
        number_clients = 1  # Number of clients banging on the server

        # Create another client simply to exit
        start = datetime.datetime.now()

        print(' Create a server, port%d' % ServerClientTest.port)
        server_proc = create_process('%s --log=%s --port=%d' % 
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        client_list = []
        for ndx in range(number_clients):
            # Create a client and send log_count logs
            client_list.append(create_process(
                '%s --count=%d --port=%d --log_msg="client %d"' %
                (LOG_CLIENT_NAME, log_count, ServerClientTest.port, ndx)))

        #import pdb; pdb.set_trace()


        print(' Wait for all %d clients to exit' % len(client_list))
        for client in client_list:
            print('getting status code for pid %r' % client.pid)
            out, err = client.communicate() # Wait for client to exit
            print(' Wait for client to terminate ')
            client_ret_code = client.wait()
            print ('status return code: %d, client: %r' % (client_ret_code, client.pid))
            if not (client_ret_code == 0):
                print ('Non-zero return: %d, client: %r', (client_ret_code, client.pid))

        print(' All clients finished. Sleep 4 sec to allow server to catch up.')
        sleeper = 4
        accum_sleep_time(sleeper)

        print(' Sending #EXIT# to the server')
        client_list.append(create_process(
            '%s --count=1 --svr-exit=true --port=%d --log_msg=#EXIT#' %
            (LOG_CLIENT_NAME, ServerClientTest.port)))

        #stop = datetime.datetime.now()
        #delta = stop - start    # Duration to send the logs
        delta = stop_timer(start, sleeper)
        print('Time to send %d logs:%s' % (number_clients*log_count, delta))

        self.assertEqual(number_clients*log_count, get_line_count(log_name))


if __name__ == '__main__':
    main()
