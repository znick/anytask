# -*- encoding: utf-8 -*-
from __future__ import nested_scopes, generators, division, absolute_import, \
    with_statement, print_function, unicode_literals

import random
import string

from app.easyCI.transliterate import ru_lang_translit_map, en_lang_translit_map, \
    transliterate, do_skip_char

__author__ = 'pahaz'


translit_map = {}
translit_map.update(ru_lang_translit_map)
translit_map.update(en_lang_translit_map)
translit_map.update({' ': '_', '_': '_', '-': '_', })
for k, v in translit_map.items():
    if v == "'":
        translit_map[k] = ''


def slugify(source_str):
    return transliterate(source_str, translit_map, do_skip_char)


def get_random_string(length=14):
    """
    >>> len(get_random_string())
    14
    >>> all(x in string.ascii_letters for x in get_random_string())
    True
    """
    return ''.join([random.choice(string.ascii_letters)
                    for _ in range(length)])
