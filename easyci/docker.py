# -*- encoding: utf-8 -*-
from __future__ import nested_scopes, generators, division, absolute_import, \
    with_statement, print_function, unicode_literals

import logging
from subprocess import Popen, PIPE
from execute3 import execute as run
from strings import get_random_string

log = logging.getLogger(__name__)


def kill_and_remove(ctr_name):
    for action in ('kill', 'rm'):
        p = Popen('docker %s %s' % (action, ctr_name), shell=True,
                  stdout=PIPE, stderr=PIPE)
        if p.wait() != 0:
            log.warning(p.stderr.read())
            # raise RuntimeError()


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
    p = run(command + cmd,
            stderr_to_stdout=True,
            # do_on_read_stdout=None,
            # do_on_read_pipeline_stderr=None,
            # do_on_read_stderr=None,
            check_return_code_and_raise_error=False,
            check_all_return_codes_in_pipeline_and_raise_error=False)

    status = p.returncode
    output = p.stdout_text
    is_timeout = status == -9 or status == 124

    if status == -9:  # Happens on timeout
        # We have to kill the container since it still runs
        # detached from Popen and we need to remove it after because
        # --rm is not working on killed containers
        kill_and_remove(name)

    return status == 0 and not is_timeout, status, is_timeout, output
