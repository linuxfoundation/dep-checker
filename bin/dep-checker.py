#!/usr/bin/python

# dep-checker - command to start/stop the Dependency Checker web interface
# Copyright 2010 Linux Foundation
# Jeff Licquia <licquia@linuxfoundation.org>

import sys
import os
import pwd
import time
import signal
import optparse

from django.core.management import execute_manager

command_line_usage = "%prog [options] start | stop"
command_line_options = [
    optparse.make_option("--force-root", action="store_true", 
                         dest="force_root", default=False,
                         help="allow running as root"),
    optparse.make_option("--server-only", action="store_true",
                         dest="server_only", default=False,
                         help="don't open a browser"),
    ]

def get_base_path():
    this_module_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(this_module_path), "compliance")

def set_import_path():
    sys.path.append(get_base_path())

def check_current_user():
    if os.getuid() == 0:
        try:
            compliance_user = pwd.getpwnam("compliance")
        except KeyError:
            sys.stderr.write("Could not find user 'compliance'.\n")
            sys.exit(1)

        os.setuid(compliance_user.pw_uid)

def start(run_browser):
    childpid = os.fork()
    if childpid == 0:
        os.setsid()

        set_import_path()
        import settings

        log_fn = os.path.join(get_base_path(), "server.log")
        try:
            log_fd = os.open(log_fn, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        except OSError:
            log_fd = -1
        if log_fd < 0:
            sys.stderr.write("Could not open log file; logging to stdout.\n")
        else:
            os.dup2(log_fd, 1)
            os.dup2(log_fd, 2)

        os.close(0)

        execute_manager(settings, ["dep-checker", "runserver"])
    else:
        pid_path = os.path.join(get_base_path(), "server.pid")
        pid_file = open(pid_path, "w")
        pid_file.write(str(childpid))
        pid_file.close()

        if run_browser:
            sys.stdout.write("Waiting for the server to start...\n")
            time.sleep(10)
            sys.stdout.write("Starting a web browser.\n")
            os.execlp("xdg-open", "xdg-open", "http://127.0.0.1:8000/linkage")
        else:
            sys.exit(0)

def stop():
    pid_path = os.path.join(get_base_path(), "server.pid")
    if os.path.exists(pid_path):
        server_pid = int(open(pid_path).read())
        sys.stdout.write("Killing process %d...\n" % server_pid)
        os.kill(server_pid, signal.SIGTERM)
        os.unlink(pid_path)
    else:
        sys.stderr.write("No server process found to stop.\n")
        sys.exit(1)

def main():
    cmdline_parser = optparse.OptionParser(usage=command_line_usage, 
                                           option_list=command_line_options)
    (options, args) = cmdline_parser.parse_args()
    if len(args) != 1 or args[0] not in ["start", "stop"]:
        cmdline_parser.error("incorrect arguments")

    # Switch users if needed.

    if args[0] == "start":
        if not options.force_root:
            check_current_user()
        start(not options.server_only)
    else:
        stop()

if __name__ == "__main__":
    main()
