import datetime
import subprocess
import sys
import os
import re

from xml.dom.minidom import parse, getDOMImplementation
from xml.parsers.expat import ExpatError

FNULL = open(os.devnull, 'w')

class SvnLog(object):
    def __init__(self, repo_url, path=""):
        url_full = repo_url + "/" + path
        proc = subprocess.Popen(['svn', '--xml', 'log', url_full], stdout=subprocess.PIPE, stderr=FNULL)
        try:
            self.xml_el = parse(proc.stdout)
        except ExpatError as e:
            self.xml_el = getDOMImplementation().createDocument(None, "not_found", None)
        proc.wait()

    def get_logs(self):
        for el in self.xml_el.getElementsByTagName("logentry"):
            log = {}
            log["author"] = ""
            log["message"] = ""
            log["revision"] = int(el.getAttribute("revision"))

            try:
                log["author"] = el.getElementsByTagName("author")[0].firstChild.nodeValue
                log["message"] = el.getElementsByTagName("msg")[0].firstChild.nodeValue
            except AttributeError:
                pass
            except IndexError:
                pass

            date_str = el.getElementsByTagName("date")[0].firstChild.nodeValue
            date_str = date_str.split(".")[0]
            log["datetime"] = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")

            yield log


class SvnDiff(object):
    class MaxSizeError(Exception):
        pass

    INDEX_RE = re.compile("^Index: (.*)")

    def __init__(self, url, path, rev_a, rev_b, max_diff_size = 0):
        self.url = url
        self.path = path
        self.rev_a = rev_a
        self.rev_b = rev_b
        self.max_diff_size = max_diff_size

    def get_diff(self):
        path_str = self.path.encode("utf-8").lstrip("/")
        proc = None
        try:
            proc = subprocess.Popen(['svn', 'diff', '-r', "{0}:{1}".format(self.rev_a, self.rev_b), self.url], stdout=subprocess.PIPE, stderr=FNULL)

            yield_line = True
            current_file_lines = 0
            current_file_too_big = False
            diff_bytes = 0
            for line in proc.stdout:
                line = line.rstrip()
                current_file_lines += 1

                m = self.INDEX_RE.search(line)
                if m:
                    current_file_lines = 0
                    current_file_too_big = False
                    diff_path = m.group(1)
                    yield_line = True

                    if path_str and not diff_path.startswith(path_str):
                        yield_line = False

                if yield_line:
                    diff_bytes += len(line)
                    yield line

                if self.max_diff_size and diff_bytes >= self.max_diff_size:
                    raise self.MaxSizeError("Diff is too big")
        except:
            if proc:
                proc.terminate()
                proc.kill()
            raise
        else:
            proc.wait()
