# task.py - task management
# Copyright 2010 Linux Foundation.
# Jeff Licquia <licquia@linuxfoundation.org>

# This task manager was originally created for the Dependency Checker
# and Code Janitor projects of the Linux Foundation.  It's fairly
# simple to use; just create a function containing the task you need
# done asynchronously, create a TaskManager object, and call its
# start() function, passing in the task function you created.  Since
# only one task at a time can be run, it's a good idea to check if
# one's already running with is_running().  Any problems (including
# trying to start a task if one's already running) cause the manager
# to throw a TaskError, so you can catch those if you need.

# Once a task is running, you can ask the manager to give you some
# simple HTML to report the task's status with read_status().  It will
# return a None object if no task is running, or a single HTML string
# suitable for embedding into a <div>.  This is designed to be
# embedded into a simple status URL that can be called with
# XMLHttpRequest and dynamically updated with JavaScript in some other
# page.

# As for reporting status, your task function can write
# specially-formatted lines to stdout or stderr.  These take the
# form:
#   TYPE: Data
# It currently supports four types: JOBDESC, MESSAGE, COUNT, and
# ITEM.  JOBDESC is a short description of the job.  COUNT and ITEM
# work together; the job is assumed to consist of COUNT items, each of
# which is reported as it is done with an ITEM line.  MESSAGE is for
# reporting the job's status when it's a little more complicated than
# "x of y items".  A MESSAGE overrides the reporting of COUNT/ITEM
# until another ITEM is received, at which point the MESSAGE is
# suppressed.

# Your task's reporting of these statuses makes its way to the
# manager's read_status() function, and is used to generate the HTML
# that function returns.

import os
try:
    import cStringIO as StringIO
except:
    import StringIO
from django.conf import settings

# Exceptions

class TaskError(StandardError):
    pass

class TaskManager:
    def __init__(self):
        self._task_log_fn = os.path.join(settings.STATE_ROOT, "task.log")
        self._task_log_file = None

    def _get_status_file(self):
        if not self.is_running():
            raise TaskError, "no task is running"

        if not self._task_log_file:
            self._task_log_file = open(self._task_log_fn)

        return self._task_log_file

    def is_running(self):
        return os.path.exists(self._task_log_fn)

    def start(self, task_func):
        if self.is_running():
            raise TaskError, "a task is already running"

        try:
            task_fd = os.open(self._task_log_fn,
                              os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        except OSError:
            raise TaskError, "could not open task log file"

        pid = os.fork()
        if pid == 0:
            pid = os.fork()
            if pid == 0:
                os.setsid()

                os.dup2(task_fd, 1)
                os.dup2(task_fd, 2)
                os.close(0)

                try:
                    task_func()
                finally:
                    os.close(task_fd)
                    os.close(1)
                    os.close(2)
                    os.unlink(self._task_log_fn)
                    os._exit(0)
            else:
                os._exit(0)
        else:
            os.waitpid(pid, 0)

    def read_status(self):
        if not self.is_running():
            return None
        else:
            jobdesc = None
            total = 0
            running_count = 0
            current = ""
            message = None
            status_str = ""
            msgadd = ""
            data = self._get_status_file().read()
            data_as_file = StringIO.StringIO(data)
            for line in data_as_file:
                if line.find(":") != -1:
                    (tag, detail) = line.split(":", 1)
                    if tag == "JOBDESC":
                        jobdesc = detail.strip()
                    elif tag == "MESSAGE":
                        message = detail.strip()
                    elif tag == "MSGADD":
                        msgadd += detail.strip() + "<br />"
                    elif tag == "COUNT":
                        total = int(detail.strip())
                    elif tag == "ITEM":
                        running_count = running_count + 1
                        current = detail.strip()
                        message = None
            if jobdesc:
                status_str = status_str + jobdesc
            if message:
                status_str = "%s<br />%s<br />" % (status_str, message)
            if msgadd:
                status_str = "%s<br />%s" % (status_str, msgadd)
            else:
                status_str = status_str + "<br />"
                if current:
                    status_str = status_str + current
                if total:
                    percent = int(float(running_count) / float(total) * 100)
                    status_str = status_str + \
"<br /><div class='bar'><div class='completed' style='width:%d%%;'></div></div>" \
                        % percent
                else:
                    status_str = "<br />Processed %d items.<br />" \
                        % (running_count - 1)
            return status_str
