#!/usr/bin/env python
#
# Test suite for command line interfaces of
# log_server.py and log_client.py
#
"""
An important idea is unittest catching sys.exit():
    with self.assertRaises(SystemExit):
    your_method()
Instances of SystemExit have an attribute code which is set
to the proposed exit status, and the context manager returned
by assertRaises has the caught exception instance as
exception, so checking the exit status is easy:

with self.assertRaises(SystemExit) as cm:
    your_method()

self.assertEqual(cm.exception.code, 1)

References:
http://docs.python.org/2/library/sys.html#sys.exit
http://lists.idyll.org/pipermail/testing-in-python/2010-August/003261.html
"""


import functools
import os
import sys
import unittest

import pdb

import log_server
import log_client

# Names of client and server python scripts.
LOG_SERVER_NAME = './log_server.py'
LOG_CLIENT_NAME = './log_client.py'


def function_name():
    # Used to highlight the currently running test.
    # Calling function name (getting the name of the previous frame)
    # For the curr func: print sys._getframe().f_code.co_name
    return sys._getframe().f_back.f_code.co_name

FCN_FMT = '\n\n========== %s =========='


def str_to_argv(str):
    """Given a string, split it into a list separate at
    each blank. This converts a string into the sys.argv
    structure.
    The string should have the exact same values
    as entered on the command line.
    """
    return str.split()


class LogServerCmdLineTest(unittest.TestCase):
    """
    Test the various options available from the command
    line to run the log_server.py.
    """

    def test_server_invalid_option(self):
        """An invalid/unknown option fails."""

        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --Xlog=log.log --log_append=False --port=5555' %
                LOG_SERVER_NAME)
        with self.assertRaises(SystemExit) as cm:
            log_server.process_cmd_line(argv[1:])
        self.assertEqual(cm.exception.code, 1)

    def test_server_invalid_port(self):
        """Pass various values of invalid ports"""

        print(FCN_FMT % function_name())

        # Non-numeric port number
        argv = str_to_argv('%s --port=%s' % (LOG_SERVER_NAME, 'abc'))
        with self.assertRaises(SystemExit) as cm:
            log_server.process_cmd_line(argv)
        self.assertEqual(cm.exception.code, 1)

    def test_server_log_append_both_ways(self):
        """Test both spellings of log-append as an option"""

        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --log-append=true')
        params = log_server.process_cmd_line(argv)
        self.assertEqual(True, params['log_append'])

        argv = str_to_argv('%s --log_append=true')
        params = log_server.process_cmd_line(argv)
        self.assertEqual(True, params['log_append'])

    def test_server_open_log_file_for_writing(self):
        """Test opening the log file.
        First, use the cmd line to create valid params.
        Second, call the open log function.
        Pass both invalid and valid moves and log names.
        """
        print(FCN_FMT % function_name())

        # Cannot write to root directory, /
        argv = str_to_argv('%s --log=/' % LOG_SERVER_NAME)
        with self.assertRaises(SystemExit) as cm:
            params = log_server.process_cmd_line(argv)
            log_server.open_log_file_for_writing(params)
        self.assertEqual(cm.exception.code, 1)

        # Cannot write to file as permission denied
        argv = str_to_argv('%s --log=/var/log/messages' % LOG_SERVER_NAME)
        with self.assertRaises(SystemExit) as cm:
            params = log_server.process_cmd_line(argv)
            log_server.open_log_file_for_writing(params)
        self.assertEqual(cm.exception.code, 1)

        # Can write to file in /tmp
        filename = '/tmp/ABCDEF'
        argv = str_to_argv('%s --log=%s --log-append=true' %
                (LOG_SERVER_NAME, filename))
        params = log_server.process_cmd_line(argv)
        log_file_handle = log_server.open_log_file_for_writing(params)
        self.assertEqual(log_file_handle.name, filename)
        self.assertEqual(params['log_append'], True)

        # Can write to file in /tmp and insist on append mode.
        filename = '/tmp/ABCDEF'
        argv = str_to_argv('%s --log=%s --log_append=false' %
            (LOG_SERVER_NAME, filename))
        params = log_server.process_cmd_line(argv)
        log_file_handle = log_server.open_log_file_for_writing(params)
        self.assertEqual(log_file_handle.name, filename)
        self.assertEqual(params['log_append'], False)

        # Can write to file in /tmp and insist on append mode.
        # Any non 'true' string results in false append.
        filename = '/tmp/ABCDEF'
        argv = str_to_argv('%s --log=%s --log_append=FooBar' %
            (LOG_SERVER_NAME, filename))
        params = log_server.process_cmd_line(argv)
        log_file_handle = log_server.open_log_file_for_writing(params)
        self.assertEqual(log_file_handle.name, filename)
        self.assertEqual(params['log_append'], False)

    def test_server_all_params_changed(self):
        """Test that all changed params get picked up"""
        print(FCN_FMT % function_name())
        filename = '/tmp/ABCDEF'
        argv = str_to_argv('%s --log=%s --log_append=blah --port=12345' %
            (LOG_SERVER_NAME, filename))
        params = log_server.process_cmd_line(argv)
        log_file_handle = log_server.open_log_file_for_writing(params)
        self.assertEqual(log_file_handle.name, filename)
        self.assertEqual(params['log_append'], False)
        self.assertEqual(params['port'], 12345)


class LogClientCmdLineTest(unittest.TestCase):
    """
    Test the various options available from the command
    line to run the log_client.py.
    """

    def test_client_invalid_option(self):
        """Try to use an invalid option"""

        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --Xport=12345' % LOG_CLIENT_NAME)
        with self.assertRaises(SystemExit) as cm:
            log_client.process_cmd_line(argv[1:])
        self.assertEqual(cm.exception.code, 1)

    def test_client_invalid_count(self):
        """Pass an invalid message count"""
        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --port=12345 --count=XYZ' % LOG_CLIENT_NAME)
        with self.assertRaises(SystemExit) as cm:
            log_client.process_cmd_line(argv[1:])
        self.assertEqual(cm.exception.code, 1)

    def test_client_valid_int_sleep(self):
        """Pass valid sleep duration"""
        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --port=12345 --sleep=2' % LOG_CLIENT_NAME)
        params = log_client.process_cmd_line(argv[1:])
        self.assertAlmostEqual(params['sleep'], 2.0)

    def test_client_valid_float_sleep(self):
        """Pass valid sleep duration"""
        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --port=12345 --sleep=1.5' % LOG_CLIENT_NAME)
        params = log_client.process_cmd_line(argv[1:])
        self.assertAlmostEqual(params['sleep'], 1.5)

    def test_client_invalid_sleep(self):
        """Pass an invalid sleep duration"""
        print(FCN_FMT % function_name())

        argv = str_to_argv('%s --port=12345 --sleep=XYZ' % LOG_CLIENT_NAME)
        with self.assertRaises(SystemExit) as cm:
            log_client.process_cmd_line(argv[1:])
        self.assertEqual(cm.exception.code, 1)

    def test_client_end_msg_to_server(self):
        """Sending EXIT_SERVER to the server changes the count to 1.
        Otherwise the client will wait to send the remainder
        of the count messages."""
        print(FCN_FMT % function_name())
        argv = str_to_argv('%s --log_msg=%s --count=10000' %
                (LOG_CLIENT_NAME, log_client.EXIT_SERVER))
        params = log_client.process_cmd_line(argv[1:])
        self.assertEqual(params['count'], 1)
        self.assertEqual(params['log_msg'], log_client.EXIT_SERVER)
        self.assertEqual(params['sleep'], 0)

    def test_client_all_params_changed(self):
        """Change all params from their defaults and check for valid"""
        print(FCN_FMT % function_name())
        port = 12345
        count = 10
        host = '192.168.1.80'
        log_msg = 'a_message'
        svr_exit = 'blah'
        sleep = 3.1416
        echo = True
        argv = str_to_argv(
            '%s --port=%d --count=%d --echo=True --sleep=3.1416 --host=%s --log_msg=%s --svr_exit=%s' %
            (LOG_CLIENT_NAME, port, count, host, log_msg, svr_exit))
        params = log_client.process_cmd_line(argv[1:])
        self.assertEqual(params['port'], port)
        self.assertEqual(params['count'], count)
        self.assertEqual(params['host'], host)
        self.assertEqual(params['log_msg'], log_msg)
        self.assertEqual(params['svr_exit'], False)
        self.assertEqual(params['echo'], True)
        self.assertAlmostEqual(params['sleep'], sleep)



if __name__ == '__main__':
    unittest.main(exit=False)
    #print 'after unittest.main()'

    sys.exit(0)

