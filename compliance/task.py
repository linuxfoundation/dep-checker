# task.py - task management
# Copyright 2010 Linux Foundation.
# Jeff Licquia <licquia@linuxfoundation.org>

import os
from django.conf import settings

# Exceptions

class TaskError(StandardError):
    pass

class TaskManager:
    def __init__(self):
        self._task_log_fn = os.path.join(settings.PROJECT_ROOT, 
                                         "compliance/task.log")
        self._task_log_file = None

    def _status_file(self):
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
