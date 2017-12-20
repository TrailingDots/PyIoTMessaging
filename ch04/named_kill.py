#!/usr/bin/python
#
# Kill all processes named in arg1
#
def usage(exit_code):
    print """
Kill or list all processes as named.
This will select processes based on the named string
which may not be the entire process name.

--kill=true/false   - If true, attempt to kill the processes
                      if false, simply list matching processes

--name=proc_name    - String for process name. If a process
                      contains that string, it gets assigned
                      for a potential kill.

For instance, debugging log_client and log_server, the
command to search for all instances of clients and server
could be obtained by the following (shortened for brevity):

ps x | egrep log_client\|log_server
19670 pts/1 S+ 0:00 grep -E --color=auto log_client|log_server
31145 pts/3 Sl 0:34 python ./log_client.py --count=10000 --log_msg=client 0
31146 pts/3 Sl 0:34 python ./log_client.py --count=10000 --log_msg=client 1
31147 pts/3 Sl 0:33 python ./log_client.py --count=10000 --log_msg=client 2
31148 pts/3 Sl 0:33 python ./log_client.py --count=10000 --log_msg=client 3

The "ps" command lists all log_client and log_servers. The script
processor is "python" and python executes "log_client".
Using --name=log_client is enough to select processes with
"log_client" on the command line.

Thus, to kill all processes with "log_client" in the
command line, use:
    named_kill.py --name=log_client --kill=true
To only list these:
    named_kill.py --name=log_client
or:
    named_kill.py --name=log_client --kill=false
    """
    sys.exit(exit_code)


import os
import sys
import pdb
import glob
import signal
import psutil

from os import listdir
from os.path import isfile, join


def find_procs_by_name(name):
    """Return a list of processes containing 'name'
    in the command line.
    The returned list consists of tuples.
    First part of tuple is the pid.
    Second part of tuple is the command line suitable for printing.
    """
    alist = []
    my_pid = os.getpid()
    for proc in psutil.process_iter(attrs=['name', 'pid', 'cmdline']):
        # Ignore this process
        if my_pid == proc.info['pid']:
            continue

        # Step through the cmdline searching for 'name'
        for item in proc.info['cmdline']:
            if name in item:
                # The system provided is an array of args in the cmdline.
                cmdline = ' '.join(proc.info['cmdline'])
                # No need to match exactly, just part of the name.
                alist.append((proc.info['pid'], cmdline))
    return alist


def process_cmd_line():
    """
    Command line code to handle user params
    """

    # Dictionary of params and defaults.
    params = {
            'kill': False,  # Do not kill process, simply list
            'name': '',     # Process name. MUST be present
            }

    import getopt
    try:
        opts, _ = getopt.gnu_getopt(
                sys.argv[1:], '',
                    ['kill=',   # 'true' to kill
                     'name=',   # name of process
                     'help'     # Print help message then exit
                    ])
    except getopt.GetoptError as err:
        print(str(err))
        usage(1)

    for opt, arg in opts:
        if opt == '--help':
            usage(0)
        if opt == '--kill':
            params['kill'] = True if 'true' == arg.lower() else False
            continue
        if opt == '--name':
            params['name'] = arg
            continue

    if len(params['name']) == 0:
        print('"--name" must have non-empty value')
        usage(1)
    return params


def kill_or_list(params, proc_list):
    """Depending upon user params, kill or list
    the processes in proc_list.
    """
    if len(proc_list) == 0:
        return

    kill = params['kill']   # True to kill process, else list
    for pid, cmdline in proc_list:
        if kill:
            os.kill(pid, signal.SIGTERM)
        else:
            print('%d\t%s' % (pid, cmdline))
    return


if __name__ == '__main__':
    params = process_cmd_line()
    proc_list = find_procs_by_name(name)
    kill_or_list(params, proc_list)
    sys.exit(0)

