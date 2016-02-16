import logging
import os
import shutil
import subprocess
import tempfile
import threading

from django.conf import settings

LOGGER = logging.getLogger('django.request')

class CheckRunner(object):
    def __init__(self, script, name, timeout=settings.EASYCI_TIMEOUT, max_output_size=1024*500):
        self.script = script
        self.name = name
        self.timeout = timeout
        self.max_output_size = max_output_size
        self._dir = tempfile.mkdtemp()

        self._script_path = os.path.join(self._dir, name + ".py")
        with open(self._script_path, "w") as fn:
            fn.write(script.encode("utf-8"))

    def __del__(self):
        if os.path.isdir(self._dir):
            shutil.rmtree(self._dir)

    def _timeout(self, proc):
        if proc.poll() is None:
            proc.terminate()
            proc.kill()
            proc._timeouted = True


    def run(self, action, student, group):
        if action not in settings.EASYCI_CHECKERS:
            LOGGER.info(u"EasyCIRUN=No checkers for this action\tCMD=%s\tSTUDENT=%s\tEXIT_CODE=%s\tOUTPUT_LEN=%s\tTRUNCATED=%s\tTIMEOUTED=%s", None, student.username, None, None, None, None)
            raise Exception("Internal error: no checkers for this action")

        checker = settings.EASYCI_CHECKERS[action]
        cmd = [checker, action, group, self.name, self._script_path]
        cwd = os.path.dirname(checker)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
        proc._timeouted = False
        t = threading.Timer(self.timeout, self._timeout, [proc])
        t.start()

        output = []
        output_current_size = 0
        truncated = False
        while True:
            buf = proc.stdout.read(1024)
            if not buf:
                break

            output_current_size += len(buf)

            if truncated:
                continue

            output.append(buf)

            if output_current_size >= self.max_output_size:
                output.append("\n[Max output size reached, output truncated!]")
                truncated = True

        t.cancel()
        if proc.poll() is None:
            proc.terminate()
            proc.kill()

        if proc._timeouted:
            output.append("\t[Timeout!]")

        exit_code = proc.wait()
        LOGGER.info(u"EasyCIRUN=OK\tCMD=%s\tSTUDENT=%s\tEXIT_CODE=%d\tOUTPUT_LEN=%d\tTRUNCATED=%s\tTIMEOUTED=%s", cmd, student.username, exit_code, output_current_size, truncated, proc._timeouted)
        return (exit_code, "".join(output))
