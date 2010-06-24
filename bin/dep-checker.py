#!/usr/bin/python

# dep-checker - command to start/stop the Dependency Checker web interface
# Copyright 2010 Linux Foundation
# Jeff Licquia <licquia@linuxfoundation.org>

import sys
import os
import time
import signal
import optparse

from django.core.management import execute_manager

command_line_usage = "%prog start | stop"
command_line_options = []

def get_base_path():
    this_module_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(this_module_path), "compliance")

def set_import_path():
    sys.path.append(get_base_path())

def start():
    childpid = os.fork()
    if childpid == 0:
        os.setsid()
        set_import_path()
        import settings
        execute_manager(settings, ["dep-checker", "runserver"])
    else:
        pid_path = os.path.join(get_base_path(), "server.pid")
        sys.stdout.write(pid_path + "\n")
        pid_file = open(pid_path, "w")
        pid_file.write(str(childpid))
        pid_file.close()

        time.sleep(10)
        os.execlp("xdg-open", "xdg-open", "http://127.0.0.1:8000/linkage")

def stop():
    pid_path = os.path.join(get_base_path(), "server.pid")
    if os.path.exists(pid_path):
        server_pid = int(open(pid_path).read())
        os.kill(server_pid, signal.SIGTERM)
    else:
        sys.stderr.write("no server process found to stop\n")
        sys.exit(1)

def main():
    cmdline_parser = optparse.OptionParser(usage=command_line_usage, 
                                           option_list=command_line_options)
    (options, args) = cmdline_parser.parse_args()
    if len(args) != 1 or args[0] not in ["start", "stop"]:
        cmdline_parser.error("incorrect arguments")
    if args[0] == "start":
        start()
    else:
        stop()

if __name__ == "__main__":
    main()
