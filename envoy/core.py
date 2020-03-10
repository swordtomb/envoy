

__version__ = "0.0.1"
__license__ = "MIT"
__author__ = "deadwind"


def _terminate_process(process):
    pass


def _kill_process(process):
    pass


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
                self.process = subprocess.Popen(self.cmd,
                                                shell=False,
                )

                # 只支持Python3
                self.out, self.err = self.process.communicate(
                    input=bytes(self.data, "utf-8") if self.data else None
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

    def __init__(self):
        pass


class Response:
    def __init__(self):
        pass


def expand_args(command):
    # 只支持py3
    if isinstance(command, str):
        splitter = shlex
    return command


def run():
    pass


def connect():
    pass

