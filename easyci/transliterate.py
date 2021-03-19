#!/usr/bin/env python3
# encoding=utf-8
from __future__ import print_function
from __future__ import unicode_literals
import string

__author__ = 'pahaz'

ru_lang_translit_map = {
    "Я": "Ja", "Ю": "Ju", 'Э': 'E', 'Ь': '\'', 'Ы': 'Y', 'Ъ': '\'', "Щ": "Sch",
    "Ш": "Sh", "Ч": "Ch", "Ц": "Ts", 'Х': 'H', 'Ф': 'F', 'У': 'U', 'Т': 'T',
    'С': 'S', 'Р': 'R', 'П': 'P', 'О': 'O', 'Н': 'N', 'М': 'M', 'Л': 'L',
    'К': 'K', 'Й': 'J', 'И': 'I', 'З': 'Z', "Ж": "Zh", 'Ё': 'E', 'Е': 'E',
    'Д': 'D', 'Г': 'G', 'В': 'V', 'Б': 'B', 'А': 'A', "я": "ja", "ю": "ju",
    'э': 'e', 'ъ': '\'', 'ы': 'y', 'ь': '\'', "щ": "sch", "ш": "sh", "ч": "ch",
    "ц": "ts", 'х': 'h', 'ф': 'f', 'у': 'u', 'т': 't', 'с': 's', 'р': 'r',
    'п': 'p', 'о': 'o', 'н': 'n', 'м': 'm', 'л': 'l', 'к': 'k', 'й': 'j',
    'и': 'i', 'з': 'z', "ж": "zh", 'ё': 'e', 'е': 'e', 'д': 'd', 'г': 'g',
    'в': 'v', 'б': 'b', 'а': 'a',
}

en_lang_translit_map = {}
for x in string.ascii_letters:
    en_lang_translit_map[x] = x

digit_translit_map = {}
for x in string.digits:
    digit_translit_map[x] = x

punctuation_and_whitespaces_translit_map = {}
for x in string.punctuation:
    punctuation_and_whitespaces_translit_map[x] = x
for x in string.whitespace:
    punctuation_and_whitespaces_translit_map[x] = ' '

allowed_filename_punctuation_and_whitespaces_translit_map = {}
for x in "!#$%&'()+,-.;=@[]^_`{}~":
    allowed_filename_punctuation_and_whitespaces_translit_map[x] = x
for x in string.whitespace:
    allowed_filename_punctuation_and_whitespaces_translit_map[x] = ' '

allowed_filename_translit_map = {}
allowed_filename_translit_map.update(allowed_filename_punctuation_and_whitespaces_translit_map)
allowed_filename_translit_map.update(ru_lang_translit_map)
allowed_filename_translit_map.update(en_lang_translit_map)
allowed_filename_translit_map.update(digit_translit_map)

ascii_translit_map = {}
ascii_translit_map.update(punctuation_and_whitespaces_translit_map)
ascii_translit_map.update(en_lang_translit_map)
ascii_translit_map.update(digit_translit_map)

ru_ascii_translit_map = {}
ru_ascii_translit_map.update(ascii_translit_map)
ru_ascii_translit_map.update(ru_lang_translit_map)


def do_skip_char(c):
    return ''


def transliterate(source_str, translit_map=ru_ascii_translit_map,
                  do_if_unknown_char=do_skip_char):
    """
    >>> transliterate('привет')
    'privet'
    """
    return ''.join(map(
        lambda x: translit_map.get(x, do_if_unknown_char(x)),
        source_str))


def safe_print(*args, **kwargs):
    """
    >>> safe_print('qwe')
    qwe
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        translited_args = tuple(transliterate(arg) for arg in args)
        print(*translited_args, **kwargs)
