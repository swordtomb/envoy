

__version__ = "0.0.1"
__license__ = "MIT"
__author__ = "deadwind"

import os
import signal
import subprocess
import threading
import shlex
import traceback
"""
目前不支持Windows和Python2
"""


def _terminate_process(process):
    os.kill(process.pid, signal.SIGTERM)


def _kill_process(process):
    os.kill(process.pid, signal.SIGKILL)


def _is_alive(thread):
    return thread.is_alive()


class Command:
    """
    封装命令并启动一个线程调用Popen执行
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self.data = None
        self.process = None
        self.out = None
        self.err = None
        self.returncode = None
        self.exc = None

    def run(self, data, timeout, kill_timeout, env, cwd):
        self.data = data
        environ = dict(os.environ)
        # 字典合并并覆盖
        environ.update(env or {})

        def target():

            try:
                self.process = subprocess.Popen(
                    self.cmd,
                    universal_newlines=True,
                    shell=False,
                    env=environ,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    cwd=cwd,
                )

                # 只支持Python3, input不传入bytes
                self.out, self.err = self.process.communicate(
                    input=self.data if self.data else None
                )
            except Exception as exc:
                self.exc = exc

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)

        if self.exc:
            raise self.exc
        if _is_alive(thread):
            _terminate_process(self.process)
            thread.join(kill_timeout)
            if _is_alive(thread):
                _kill_process(self.process)
                thread.join()

        self.returncode = self.process.returncode
        return self.out, self.err


class ConnectedCommand:

    def __init__(self, process=None, std_in=None, std_out=None, std_err=None):
        self._process = process
        self.std_in = std_in
        self.std_out = std_out
        self.std_err = std_err
        self._status_code = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill()

    @property
    def status_code(self):
        return self._status_code

    @property
    def pid(self):
        return self._process.pid

    def kill(self):
        return self._process.kill()

    def expect(self, b, stream=None):
        if stream is None:
            stream = self.std_out

    def send(self, string, end='\n'):
        return self._process.stdin.write(string + end)

    def block(self):
        self._status_code = self._process.wait()


class Response:
    """
    命令返回
    """
    def __init__(self, process=None):
        self._process = process
        self.command = None
        self.std_err = None
        self.std_out = None
        self.status_code = None
        self.history = []

    def __repr__(self):
        if len(self.command):
            return f"<Response [{self.command[0]}]>"
        else:
            return "<Response>"


def expand_args(command):
    # 只支持py3
    if isinstance(command, str):
        # command.encode("utf-8")?splitter
        splitter = shlex.shlex(command)
        splitter.whitespace = '|'
        splitter.whitespace_split = True
        command = []

        while True:
            token = splitter.get_token()
            if token:
                command.append(token)
            else:
                break

        command = [shlex.split(x) for x in command]
    return command


def run(command, data=None, timeout=None, kill_timeout=None, env=None, cwd=None):
    """

    """
    command = expand_args(command)

    history = []
    for c in command:
        if len(history):
            # 处理破管问题(broken pipe)
            # data = history[-1].std_out[0:10*1024]
            data = history[-1].std_out[:10*1024]
        cmd = Command(c)
        try:
            out, err = cmd.run(data, timeout, kill_timeout, env, cwd)
            status_code = cmd.returncode
        except OSError as e:
            out, err = '', '\n'.join([e.strerror, traceback.format_exc()])
            status_code = 127

        r = Response(process=cmd)

        r.command = c
        r.std_out = out
        r.std_err = err
        r.status_code = status_code

        history.append(r)

    r = history.pop()
    r.history = history

    return r


def connect(command, data=None, env=None, cwd=None):

    # TODO support piped commands
    command_str = expand_args(command).pop()
    environ = dict(os.environ)
    environ.update(env or {})

    process = subprocess.Popen(
        command_str,
        universal_newlines=True,
        shell=False,
        env=environ,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        cwd=cwd
    )

    return ConnectedCommand(process=process)

if __name__ == "__main__":

    r = run("echo -n 'hi' | tr '[:lower:]' '[:upper:]'")
    print("?")
    print(r.std_out)
    print(r.std_err)
    print(r.status_code)
