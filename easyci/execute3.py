"""This module is wrapper for subprocess which aims to make life easier for
anyone who needs to interact with shell commands from Python code.

"""
import time
import os
import subprocess
import threading
import shlex
import sys
import logging
import types

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

if PY3:
    string_types = str,
elif PY2:
    string_types = basestring,
else:
    raise RuntimeError('Unknown python string_types')

try:
    from subprocess import TimeoutExpired as BaseTimeoutClass  # New in v. 3.3.
except ImportError:
    BaseTimeoutClass = Exception

__author__ = 'pahaz'

log = logging.getLogger(__name__)
READER__MAX_READ_SIZE = 2048
EXECUTE__MAX_BUFFER_SIZE_IF_USE_TRUNCATED_BUFFER = READER__MAX_READ_SIZE * 4
_index = 0
_lock = threading.Lock()


def _get_uid():
    global _index
    with _lock:
        i = _index
        _index += 1
    return i


class BaseExecuteCommandError(Exception):
    """Base exception for execute module.
    """


class ExecuteCommandParseError(BaseExecuteCommandError):
    """This exception is raised when the command parser find execution problem.
    """


class ExecuteCommandBaseExecutionError(BaseExecuteCommandError):
    """This base exception for errors when the command execution problem.
    """

    def set_stdout_stderr_and_update_output(self, stdout_bytes, stderr_bytes):
        self.stderr = stderr_bytes
        self.stdout = stdout_bytes
        self.output = "STDOUT: {0}\nSTDERR: {1}".format(
            _repr_bytes(stdout_bytes),
            _repr_bytes(stderr_bytes))


class ExecuteCommandNonZeroExitStatus(subprocess.CalledProcessError,
                                      ExecuteCommandBaseExecutionError):
    """This exception is raised when a process returns a non-zero exit status.
    """

    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stdout = None
        self.stderr = None

    def __str__(self):
        return "Command '{0}' returned non-zero exit status {1}\n{2}" \
            .format(self.cmd, self.returncode, self.output)


class ExecuteCommandPipelineNonZeroExitStatus(ExecuteCommandNonZeroExitStatus):
    """This exception is raised when a process pipeline returns a non-zero exit
    status.
    """


class ExecuteCommandTimeoutExpired(ExecuteCommandBaseExecutionError,
                                   BaseTimeoutClass):
    """This exception is raised when the timeout expires while waiting
    for a child process.
    """

    def __init__(self, cmd, timeout, output=None):
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stdout = None
        self.stderr = None
        self.encoding = 'utf-8'

    def __str__(self):
        return ("Command '{0}' timed out after {1} seconds\n{2}"
                .format(self.cmd, self.timeout, self.output))

    @property
    def stdout_text(self):
        return self.stdout

    @property
    def stderr_text(self):
        return self.stderr


def shlex_split_and_group_by_commands(cmd):
    """Splits in the sub-command

    Examples:

        >>> shlex_split_and_group_by_commands("echo test")
        [{'cmd': ['echo', 'test'], 'out': None, 'err': None}]
        >>> shlex_split_and_group_by_commands("cat | python")
        [{'cmd': ['cat'], 'out': subprocess.PIPE, 'err': None},
         {'cmd': ['python'], 'out': None, 'err': None}]
        >>> shlex_split_and_group_by_commands("cat > file.txt")
        [{'cmd': ['cat'], 'out': {'file': 'aaa', 'mode': 'wb'}, 'err': None}]
        >>> shlex_split_and_group_by_commands(["echo", "test"])
        [{'cmd': ['echo', 'test'], 'err': None, 'out': None}]

    :param cmd: command
    :return: list of commands
    """
    if not cmd:
        raise ExecuteCommandParseError('No command for execute')

    PIPELINES = '|', '|&', '&|'
    REDIRECTS = '>', '1>', '2>', '&>', '1>>', '>>', '&>>', '2>>'
    UNEXPECTED_TOKENS = ['&&', '||']
    make_new_command = lambda: {'cmd': [], 'out': None, 'err': None}
    if isinstance(cmd, (list, tuple)):
        tokens = cmd
    else:
        tokens = shlex.split(cmd)

    for x in UNEXPECTED_TOKENS:
        if x in tokens:
            raise ExecuteCommandParseError("Parser does not know how to work "
                                           "with '{0}' in commands".format(x))

    commands = []
    current_cmd = make_new_command()
    current_cmd_stop = False
    tokens_iter = iter(tokens)
    for x in tokens_iter:
        if x in REDIRECTS:
            try:
                target = next(tokens_iter)
            except StopIteration:
                raise ExecuteCommandParseError(
                    'Unexpected EOF. No target for redirection')
            if not current_cmd['cmd']:
                raise ExecuteCommandParseError(
                    'Unexpected redirection. No command for redirection')
            _update_redirection(x, current_cmd, target)
            current_cmd_stop = True

        elif x in PIPELINES:
            if not current_cmd['cmd']:
                raise ExecuteCommandParseError(
                    'Unexpected pipeline. No command for pipeline')

            _update_pipeline(x, current_cmd)
            commands.append(current_cmd)
            current_cmd = make_new_command()
            current_cmd_stop = False

        else:
            if current_cmd_stop:
                raise ExecuteCommandParseError(
                    'Command continuation after redirection')
            current_cmd['cmd'].append(x)

    if current_cmd['cmd']:
        commands.append(current_cmd)

    # check pipeline in end of command
    if commands[-1]['out'] == subprocess.PIPE:
        raise ExecuteCommandParseError(
            'Pipeline in end of commands')

    # check stdout != None
    for c in commands[:-1]:
        if c['out'] is None:
            raise ExecuteCommandParseError(
                "None stdout in command sequence")

    return commands


def do_write_stdout(x):
    sys.stdout.write(x)
    sys.stdout.flush()


def do_write_stderr(x):
    sys.stderr.write(x)
    sys.stderr.flush()


def base_execute(
        cmd, input=None, shell=False, env=None, cwd=None,
        stderr_to_stdout=False,
        do_on_read_stdout=do_write_stdout,
        do_on_read_stderr=do_write_stderr,
        do_on_read_pipeline_stderr=do_write_stderr,
        timeout=None,
        kill_timeout=None,
):
    if input and not isinstance(input, types.GeneratorType):
        raise TypeError('input argument must be a generator')

    index = _get_uid()

    start_time = time.time()
    log.info("Start time: %s uid=%s", start_time, index)

    opened_fds = []
    processes = []
    threads = []
    try:
        STDOUT_or_PIPE = subprocess.STDOUT if stderr_to_stdout else \
            subprocess.PIPE

        if shell:
            commands = [{'cmd': cmd, 'err': None, 'out': None}]
        else:
            commands = shlex_split_and_group_by_commands(cmd)

        commands[-1]['out'] = _process_out_and_err(
            commands[-1]['out'], opened_fds, subprocess.PIPE)
        commands[-1]['err'] = _process_out_and_err(
            commands[-1]['err'], opened_fds, STDOUT_or_PIPE)

        last_stdout = subprocess.PIPE if input else None

        read_end, default_out = os.pipe()
        read_end = os.fdopen(read_end, 'rb', 2048)
        default_out = os.fdopen(default_out, 'wb', 2048)
        opened_fds.append(default_out)
        opened_fds.append(read_end)

        default_out = None

        for i, command in enumerate(commands):
            log.info("Running p%d %r uid=%s", i, command, index)
            out = _process_out_and_err(command['out'], opened_fds, default_out)
            err = _process_out_and_err(command['err'], opened_fds, default_out)
            args = command['cmd']

            process = subprocess.Popen(args, stdout=out, stderr=err,
                                       stdin=last_stdout, shell=shell, env=env,
                                       cwd=cwd)
            process.args = args
            process.printable_args = _printable_args(args)
            processes.append(process)
            last_stdout = process.stdout

        last_process = processes[-1]
        first_process = processes[0]

        threads_info__fd__action__name__target = (
            (last_process.stderr, do_on_read_stderr, 'stderr-reader', _reader),
            (last_process.stdout, do_on_read_stdout, 'stdout-reader', _reader),
            (read_end, do_on_read_pipeline_stderr, 'pipe-err-reader', _reader),
            (first_process.stdin, input, 'stdin-writer', _writer),
        )

        for fd, action, name, target in threads_info__fd__action__name__target:
            if fd:
                thread_name = threading._newname(name + "-thread-%d")
                thread = threading.Thread(target=target,
                                          args=(fd, action, thread_name),
                                          name=thread_name)
                threads.append(thread)
                log.info('Starting %s uid=%s', thread_name, index)
                thread.start()
            else:
                log.info('Skip %s-thread uid=%s', name, index)

        log.info('Waiting command execution uid=%s', index)
        _wait_with_timeout(last_process, timeout, cmd, index)

    finally:
        log.info('Polling processes uid=%s', index)
        for i, process in enumerate(processes):
            process.poll()
            log.debug("Process p%d returncode %r uid=%s",
                      i, process.returncode, index)
            if process.returncode is None:
                log.info("Terminating process p%d uid=%s", i, index)
                process.terminate()
                # wait and kill !

        if kill_timeout is not None:
            log.warning('Killing processes! kill_timeout=%s uid=%s',
                        kill_timeout, index)
            time.sleep(kill_timeout)
            for i, process in enumerate(processes):
                process.poll()
                if process.returncode is None:
                    log.info("Kill process p%d uid=%s", i, index)
                    process.kill()

        log.info('Closing process in/out/err descriptors uid=%s', index)
        for i, process in enumerate(processes):
            for fd_name, fd in (('in', process.stdin), ('out', process.stdout),
                                ('err', process.stderr)):
                if fd and not fd.closed:
                    log.info('Close %s for p%d uid=%s', fd_name, i, index)
                    _safe_close(fd, index)

        log.info('Closing descriptors uid=%s', index)
        for fd in opened_fds:
            _safe_close(fd, index)

        for thread in threads:
            status = "alive" if thread.is_alive() else "stopped"
            log.debug("Waiting thread %s %s uid=%s", status,
                      thread.name, index)
            thread.join()

        finally_time = time.time()
        log.info("Finally time: %s (+%s) uid=%s",
                 finally_time, finally_time - start_time, index)

    return [process.returncode for process in processes]


class ExecuteResult(object):
    def __init__(self, cmd, returncodes, stdout, stderr, pipeline_stderr):
        self.cmd = cmd
        self.returncodes = returncodes
        self.stdout = stdout
        self.stderr = stderr
        self.pipeline_stderr = pipeline_stderr
        self.encoding = 'utf-8'

    @property
    def returncode(self):
        return self.returncodes[-1]

    @property
    def stdout_text(self):
        return self.stdout.decode(self.encoding)

    @property
    def stderr_text(self):
        return self.stderr.decode(self.encoding)

    @property
    def pipeline_stderr_text(self):
        return self.pipeline_stderr.decode(self.encoding)


def execute(
        cmd, input=None, shell=False, env=None, cwd=None,
        stderr_to_stdout=False,
        do_on_read_stdout=do_write_stdout,
        do_on_read_stderr=do_write_stderr,
        do_on_read_pipeline_stderr=do_write_stderr,
        timeout=None,

        use_truncated_buffer_for_stdout=False,
        use_truncated_buffer_for_stderr=False,
        use_truncated_buffer_for_pipeline_stderr=False,

        check_return_code_and_raise_error=True,
        check_all_return_codes_in_pipeline_and_raise_error=True,
        kill_processes_after_timeout=True,
):
    """Execute shell command.

    If command produce large output use truncated_buffer for collecting only
    last bytes.

    :param cmd: command may contain pipes
    :param input: generator object
    :param shell: use shell (False = secure)
    :param env: environment
    :param cwd: current work dir
    :param stderr_to_stdout: redirect stderr to stdout
    :param do_on_read_stdout: function for do some work with the stdout bytes
    :param do_on_read_stderr: function for do some work with the stderr bytes
    :param do_on_read_pipeline_stderr: function for do some work with bytes
    read form the pipeline stderr bytes stream.
    :param timeout: timeout in seconds
    :param use_truncated_buffer_for_stdout: collect stdout to truncated_buffer
    :param use_truncated_buffer_for_stderr: collect stderr to truncated_buffer
    :param use_truncated_buffer_for_pipeline_stderr: use truncated_buffer
    :param check_return_code_and_raise_error: raise error if return code != 0
    :param check_all_return_codes_in_pipeline_and_raise_error: raise error
    if one of pipeline return codes != 0
    :return: ExecuteResult
    """
    # TODO: add convert str to bytes in generator!
    stdout = _ReaderWrapper(do_on_read_stdout, use_truncated_buffer_for_stdout)
    stderr = _ReaderWrapper(do_on_read_stderr, use_truncated_buffer_for_stderr)
    pipeline_stderr = _ReaderWrapper(do_on_read_pipeline_stderr,
                                     use_truncated_buffer_for_pipeline_stderr)

    try:
        kill_timeout = 1 if timeout and kill_processes_after_timeout else None
        returncodes = base_execute(
            cmd, input=input, shell=shell, env=env, cwd=cwd,
            stderr_to_stdout=stderr_to_stdout,
            do_on_read_stderr=stderr.do_on_read,
            do_on_read_stdout=stdout.do_on_read,
            do_on_read_pipeline_stderr=pipeline_stderr.do_on_read,
            timeout=timeout,
            kill_timeout=kill_timeout,
        )
    except ExecuteCommandTimeoutExpired as err:
        err.set_stdout_stderr_and_update_output(stdout.get_bytes_data(),
                                                stderr.get_bytes_data())
        raise

    retcode = returncodes[-1]
    stdout_bytes = stdout.get_bytes_data()
    stderr_bytes = stderr.get_bytes_data()
    pipeline_stderr_bytes = pipeline_stderr.get_bytes_data()

    if check_return_code_and_raise_error or \
            check_all_return_codes_in_pipeline_and_raise_error:
        err = None
        if check_return_code_and_raise_error and retcode != 0:
            err = ExecuteCommandNonZeroExitStatus(retcode, cmd)

        if check_all_return_codes_in_pipeline_and_raise_error:
            for code in returncodes[:-1]:
                if code != 0:
                    err = ExecuteCommandPipelineNonZeroExitStatus(retcode, cmd)
                    break
        if err:
            err.set_stdout_stderr_and_update_output(stdout.get_bytes_data(),
                                                    stderr.get_bytes_data())
            raise err

    return ExecuteResult(cmd, returncodes, stdout_bytes, stderr_bytes,
                         pipeline_stderr_bytes)


def _reader(fd, action, thread_name):
    log.debug('{name}: start reader'.format(name=thread_name))
    while 1:
        try:
            a = fd.read(READER__MAX_READ_SIZE)
        except ValueError as e:
            # ValueError: read of closed file
            # raises in perr-thread because pipe descriptor closes faster
            # than read understand it
            log.debug('{name}: ValueError: {0}'
                      .format(repr(e), name=thread_name))
            a = b''

        log.debug('{name}: read: {0}'.format(repr(a), name=thread_name))

        try:
            if action and callable(action):
                action(a)
        except Exception as e:
            log.exception("{name}: exception while do read action: {0}"
                          .format(str(e), name=thread_name))

        if not a:
            break

    log.debug('{name}: finish reader'.format(name=thread_name))


def _writer(fd, generator, thread_name):
    log.debug('{name}: start writer'.format(name=thread_name))
    try:
        for x in generator:
            log.debug('{name}: write: {0}'
                      .format(repr(x), name=thread_name))

            fd.write(x)
            fd.flush()

    finally:
        fd.close()

    log.debug('{name}: finish writer'.format(name=thread_name))


def _repr_bytes(x):
    r = repr(x)[2:-1]
    for old, new in (('\\n', '\n'), ('\\r', '\r'), ('\\t', '\t')):
        r.replace(old, new)
    return r


def _printable_args(args):
    if isinstance(args, string_types):
        return args
    args = [(repr(x) if ' ' in x else x) for x in args]
    return repr(' '.join(args))[1:-1]


class _ReaderWrapper(object):
    def __init__(self, do_on_read=None, is_use_truncated_buffer=False):
        self.__is_use_truncated_buffer = is_use_truncated_buffer
        self.__do_on_read = do_on_read
        self.__buffer = bytearray()

    def do_on_read(self, x):
        self.__buffer.extend(x)
        if self.__is_use_truncated_buffer:
            max_size = EXECUTE__MAX_BUFFER_SIZE_IF_USE_TRUNCATED_BUFFER
            self.__buffer = self.__buffer[-max_size:]

        try:
            action = self.__do_on_read
            if action and callable(action):
                action(x)
        except Exception as e:
            log.exception("{name}: exception while do read action: {0}"
                          .format(str(e), name='ByteDataCollectorWrapper'))

    def get_bytes_data(self):
        return bytes(self.__buffer)


def _update_redirection(redirection, cmd, target):
    std_map = {
        '>': ('out', 'wb'),
        '1>': ('out', 'wb'),
        '2>': ('err', 'wb'),
        '>>': ('out', 'ab'),
        '1>>': ('out', 'ab'),
        '2>>': ('err', 'ab'),
        '&>': ('err_and_out', 'wb'),
        '&>>': ('err_and_out', 'ab'),
    }
    if redirection in ['>', '1>', '2>', '>>', '1>>', '2>>']:
        std, mode = std_map[redirection]
        if cmd[std] is not None:
            raise ExecuteCommandParseError(
                'Override redirection. {0} to {1}'
                .format(cmd[std], target))
        cmd[std] = {'file': target, 'mode': mode}
    elif redirection in ['&>', '&>>']:
        _, mode = std_map[redirection]
        if cmd['out'] is not None or cmd['err'] is not None:
            raise ExecuteCommandParseError(
                'Override redirection. {0} and {1} to {2}'
                .format(cmd['out'], cmd['err'], target))
        cmd['err'] = subprocess.STDOUT
        cmd['out'] = {'file': target, 'mode': mode}
    else:
        raise ExecuteCommandParseError(
            'Unknown redirection {0}'
            .format(redirection))


def _update_pipeline(pipeline, cmd):
    if pipeline in ['|&', '&|']:
        if cmd['out'] is not None or cmd['err'] is not None:
            raise ExecuteCommandParseError(
                'Override redirection by pipeline. Used {0} and {1}'
                .format(cmd['out'], cmd['err']))
        cmd['err'] = subprocess.STDOUT
        cmd['out'] = subprocess.PIPE
    elif pipeline in ['|']:
        if cmd['out'] is not None:
            raise ExecuteCommandParseError(
                'Override redirection by pipeline. Used {0}'
                .format(cmd['out']))
        cmd['out'] = subprocess.PIPE


def _process_out_and_err(fd, opened_fds, default_fd):
    if isinstance(fd, dict):
        f = open(fd['file'], fd['mode'])
        opened_fds.append(f)
        return f
    elif fd is None:
        return default_fd
    return fd


def _safe_close(x, index):
    try:
        x.close()
    except Exception as e:
        log.exception("Exception while close fd: %r uid=%s", e, index)


def _wait_with_timeout(last_process, timeout, cmd, index):
    if sys.version_info[:2] < (3, 3):
        start = time.time()
        while last_process.returncode is None:
            last_process.poll()
            now = time.time()
            if timeout and now - start > timeout:
                log.warning('TIMEOUT uid=%s', index)
                raise ExecuteCommandTimeoutExpired(cmd, timeout)
            time.sleep(0.3)
    else:
        try:
            last_process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            log.warning('TIMEOUT uid=%s', index)
            raise ExecuteCommandTimeoutExpired(e.cmd, e.timeout)