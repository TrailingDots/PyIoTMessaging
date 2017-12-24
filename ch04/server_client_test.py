#!/usr/bin/env python
#
# Test suite for log_server.py and log_client.py
#
# If any tests hang, run this in a terminal to find
# the hanging processes:
#    ps aux | egrep log_client\|log_server
#
# After running these tests, the above command line
# should run and indicate *no* hanging processes
# as a result of these integration tests.
#

import datetime         # for timing
import functools
import os
import sys
import subprocess       # To spawn subprocesses
import time
import unittest

from listening_port import listening, is_listening
import log_client 
import log_server
from named_kill import find_procs_by_name

# Names of client and server python scripts.
LOG_SERVER_NAME = './log_server.py'
LOG_CLIENT_NAME = './log_client.py'

# NOISY == True prints trace messages that might
# assist in debugging.
NOISY = True


def function_name():
    # function (getting the name of the previous frame)
    # For the curr func: print sys._getframe().f_code.co_name
    return sys._getframe().f_back.f_code.co_name


def print_function_name():
    print('\n\n========== %s ==========' % function_name())

class ServerCmdLineTest(unittest.TestCase):
    """Test the various options available from the command
    line to run the log_server.py.
    """
    import log_server

    def setUp(self):
        kill_listening_processes(ServerClientTest.port)

    # In testing for invalid command line operations,
    # this should always be None, meaning the log_server
    # could not start.
    log_server_proc = None


    def test_echo(self):

        print('\n\n========== %s ==========' % function_name())

        proc = create_process_with_stderr(
                ['/usr/bin/echo', 'hello world'])
        print('proc:%r', proc)
        print('proc_dict__:%r', proc.__dict__)

        xproc = create_process_with_stderr(
                '/usr/bin/Xecho hello world')
        print('xproc:%r', xproc)
        print('xproc_dict__:%r', xproc.__dict__)


    def test_invalid_option(self):
        """An invalid/unknown option fails."""

        print('\n\n========== %s ==========' % function_name())


        # Attempt to create a server with an invalid option
        # No such option: --Xlog
        log_server_proc = create_process_with_stderr(
                '%s --Xlog=%s --log_append=False --port=5555' %
            (LOG_SERVER_NAME, 'log.log'))
        self.assertEqual(0, log_server_proc.returncode)


    def test_invalid_port(self):
        """Pass various values of invalid ports"""

        print('\n\n========== %s ==========' % function_name())

        # Non-numeric port number
        bad_port_proc = create_process_with_stderr('%s --port=%s' %
            (LOG_SERVER_NAME, 'abc'))
        print('bad_port_proc:%r' % bad_port_proc.__dict__)


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
    """Create a subprocess and start it running."""
    if NOISY:
        print('create_process:%r' % cmd_line)
    proc = subprocess.Popen(cmd_line, shell=True)
    return proc

def create_process_with_stderr(cmd_line):
    """Create a process with stderr sent to stdout.
    Start it running but don't wait.
    Generally use for test that expect to fail."""
    #import pdb; pdb.set_trace()
    time.sleep(1)
    if NOISY:
        print('create_process_with_stderr %s' % cmd_line)
    try:
        proc = subprocess.Popen(cmd_line, 
                                shell=True,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        print('ERROR:CalledProcessError: %s' % err)
        return -1
    except Exception as err:
        print('ERROR:Error: %s' % err)
        return -2
    else:
        # Process ran. Got something as output.
        print('output:\n%s' % proc)
    finally:
        time.sleep(1)

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

    if NOISY:
        print('wc_out:%s' % wc_out)
    try:
        wc_count = int(wc_out.split(' ')[0])
    except ValueError:
        print('unexpected value in return from wc:%s:' % (err, wc_out))
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


def get_line_count(log_name):
    """Given a log file name, 
    answer the number of lines in that log file.
    """

    data = load_file(log_name)

    """
     Log file must have 'count' lines.
     This could be better - could use regex to determine
     if the logged data meets expectations.
    """
    return  count_lines_in_file(log_name)

@unittest.skip('skipping ServerClientTest')
class ServerClientTest(unittest.TestCase):

    # Port value used by all tests.
    port = 5555

    def setUp(self):
        kill_listening_processes(ServerClientTest.port)

    def test_happy_path(self):
        """Test the happy path where parameters
        provide a simple and happy logging environment.

        python -m unittest server_client_test.ServerClientTest.test_happy_path
        """

        print function_name()

        log_name = 'happy.log'
        count = 10  # logs from client to server

        # Create a server
        server_proc = create_process('%s --log=%s --log_append=False --port=%d' %
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        # Create a client and send logs
        client_proc = create_process('%s --svr-exit=true --count=%d --port=%d' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))
        time.sleep(1)
        self.assertEqual(count, get_line_count(log_name))


    def test_two_clients(self):
        """A happy path where 2 clients log with parameters
        that should cause no problems.
        """

        print function_name()

        log_name = '2clients.log'
        count = 10000   # 10k logs
        sleeper = 4     # Sleep time to allow server to process.

        # Create a client and send count logs
        client_proc1 = create_process('%s --count=%d --port=%d --log_msg=Client1' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))

        # Create another client and send count logs
        client_proc2 = create_process('%s --count=%d --port=%d --log_msg=Client2' %
            (LOG_CLIENT_NAME, count, ServerClientTest.port))

        # Create a server
        server_proc = create_process('%s --log_append=False --log=%s --port=%d' % 
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        # Wait for the 2 clients to terminate
        client_proc1.communicate()
        client_proc2.communicate()

        # Need to sleep because the server has not had time
        # to process all the logs.
        accum_sleep_time(sleeper)

        # Create another client simply to exit
        # If the sleep time is too short, the buffered logs
        # in the server get dropped. This yields a false negative.
        client_exit = create_process('%s --svr-exit=true --count=1 --port=%d --log_msg=@EXIT@ test_two_clients' %
            (LOG_CLIENT_NAME, ServerClientTest.port))

        self.assertEqual(2*count, get_line_count(log_name))

    '''
    def test_timing_100k(self):
        """Time sending 10000 simple logs."""
        log_count = 100000    # Number of l0gs to send.
        log_name = '100k.log'
        sleeper = 15          # Time to sleep and let the server write the data.
        print function_name()


        start = datetime.datetime.now()

        # Create a client and send logs
        client_proc1 = create_process('%s --svr_exit=true --count=%d --port=%d --log_msg="100k logs"' %
            (LOG_CLIENT_NAME, log_count, ServerClientTest.port))

        # Create a server
        server_proc = create_process('%s --log_append=False --log=%s --port=%d' %
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        accum_sleep_time(sleeper)

        delta = stop_timer(start, sleeper)
        print('Time to send %d logs:%s' % (log_count, delta))

        self.assertEqual(log_count, get_line_count(log_name) )
    '''

    def test_timing_10k_20clients(self):
        """Time sending 1000 logs from each of 20 clients."""

        log_count = 1000     # Number of l0gs to send.
        log_name = '20client.log'
        number_clients = 10  # Number of clients banging on the server
        sleeper = 4          # Time is sec to let server write lots.

        print function_name()

        # Create another client simply to exit
        start = datetime.datetime.now()

        if NOISY:
            print(' Create a server, port%d' % ServerClientTest.port)
        server_proc = create_process('%s --log_append=False --log=%s --port=%d' %
            (LOG_SERVER_NAME, log_name, ServerClientTest.port))

        client_list = []
        for ndx in range(number_clients):
            # Create a client and send log_count logs
            client_list.append(create_process(
                '%s --count=%d --port=%d --log_msg="client %d"' %
                (LOG_CLIENT_NAME, log_count, ServerClientTest.port, ndx)))

        if NOISY:
            print(' Wait for all %d clients to exit' % len(client_list))
        for client in client_list:
            out, err = client.communicate()     # Wait for client to exit
            client_ret_code = client.wait()
            if NOISY:
                print('status return code: %d, client: %r' % (client_ret_code, client.pid))
            if not (client_ret_code == 0):
                print('Non-zero return: %d, client: %r', (client_ret_code, client.pid))

        if NOISY:
            print(' All clients finished. Sleep 4 sec to allow server to catch up.')
        accum_sleep_time(sleeper)

        if NOISY:
            print(' Sending @EXIT@ to the server')
        client_list.append(create_process(
            '%s --count=1 --svr-exit=true --port=%d --log_msg=@EXIT@ test_timing_10k_20clients' %
            (LOG_CLIENT_NAME, ServerClientTest.port)))

        delta = stop_timer(start, sleeper)
        print('Time to send %d logs:%s' % (number_clients*log_count, delta))

        self.assertEqual(number_clients*log_count, get_line_count(log_name))


def list_hanging_processes():
    """List any hanging processes related to these tests.
    This test provides only a rough guess as it does not
    account for our port assignment. Other ports may
    get included if they seek active processing.

    The caller must decide if these reported processes
    must be killed.

    Returns count of hanging processes.
    """

    print('\n-----------------\nlist_hanging_processes:')
    hanging = 0
    for proc in ['log_client', 'log_server']:
        pid_list = find_procs_by_name('log_client')
        for pid, cmdline in pid_list:
            hanging += 1
            print('%s\t%s' % (pid, cmdline))
    return hanging


if __name__ == '__main__':
    unittest.main(exit=False)

    # Ensure that no hanging processes exist.
    hanging = list_hanging_processes()
    print('Number of hanging processes: %d' % hanging)
    sys.exit(0)

