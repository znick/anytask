# -*- encoding: utf-8 -*-
from __future__ import nested_scopes, generators, division, absolute_import, \
    with_statement, print_function, unicode_literals

import logging
from subprocess import Popen, PIPE
from strings import get_random_string
from io import StringIO
import threading
import subprocess


log = logging.getLogger(__name__)

BUF_SIZE = 4096
LIMIT_BYTES = 10 * 1024 * 1024


def kill_and_remove(ctr_name):
    for action in ('kill', 'rm'):
        p = Popen('docker %s %s' % (action, ctr_name), shell=True,
                  stdout=PIPE, stderr=PIPE)
        if p.wait() != 0:
            log.warning(p.stderr.read())
            # raise RuntimeError()


def limited_reader(fn_in, fn_out, limit_bytes):
    read_bytes = 0
    truncated = False
    while True:
        buf = fn_in.read(BUF_SIZE)
        if len(buf) == 0:
            break

        if read_bytes >= limit_bytes and not truncated:
            fn_out.write("\nTRUNCATED\n")
            truncated = True

        read_bytes += len(buf)
        if not truncated:
            fn_out.write(buf.decode("utf-8"))


def execute(cmd, user="nobody", cwd=None, timeout=None, network='none',
            memory_limit=str('1024m'),
            image='ubuntu:14.04', volumes=None, name_prefix=''):
    if not isinstance(cmd, list):
        raise TypeError('cmd argument is not a list')
    if volumes is not None and not isinstance(volumes, list):
        raise TypeError('volumes argument is not a list')
    if timeout is not None and not isinstance(timeout, (float, int)):
        raise TypeError('timeout argument is not a float')
    if memory_limit is not None:
        if not isinstance(memory_limit, str):
            raise TypeError('memory_limit argument is not a str')
        if not memory_limit or memory_limit[-1] not in 'bkmg':
            raise ValueError('memory_limit argument invalid (use '
                             '<number><unit> format, where unit can be one of '
                             'b, k, m, or g)')
    if cwd is None:
        cwd = '/'

    name = get_random_string()

    command = []

    if timeout:
        # timeout docker run
        command += ['timeout', '-k', str(timeout + 3), str(timeout + 2)]

    command += ['docker', 'run', '--rm', '--name', name_prefix + name]
    if network != 'bridge':
        command += ['--net', network]
    if user != 'root':
        command += ['-u', user]
    if cwd != '/':
        command += ['-w', cwd]
    if volumes:
        for v in volumes:
            command += ['-v', v]
    if memory_limit:
        command += ['-m', memory_limit]

    command += [image]

    if timeout:
        # timeout in docker run
        command += ['timeout', '-k', str(timeout + 1), str(timeout)]

    logging.info("Will run: %s", command + cmd)
    p = subprocess.Popen(command + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = StringIO()
    t1 = threading.Thread(target=limited_reader, args=(p.stdout, output, LIMIT_BYTES))
    t2 = threading.Thread(target=limited_reader, args=(p.stderr, output, LIMIT_BYTES))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    p.wait()

    status = p.returncode
    output = output.getvalue()
    is_timeout = status == -9 or status == 124

    if status == -9:  # Happens on timeout
        # We have to kill the container since it still runs
        # detached from Popen and we need to remove it after because
        # --rm is not working on killed containers
        kill_and_remove(name)

    return status == 0 and not is_timeout, status, is_timeout, output
