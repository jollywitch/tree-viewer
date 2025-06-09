import os
import sys
from pathlib import Path
from enum import Enum

MAX_LEVEL = 10
MAX_DEGREE = 20
START_PATH = "."
STATE = {}

class ReceivingType(Enum):
    SET_MAX_LEVEL = 1
    SET_MAX_DEGREE = 2
    SET_START_PATH = 3
    SHOW_STATUS = 4
    ITERATE_ALL = 5

def initialize_argv():
    global MAX_LEVEL, MAX_DEGREE, START_PATH, STATE

    STATE['receiving'] = None
    for chunk in sys.argv[1:]:
        if STATE['receiving']:
            if STATE['receiving'] == ReceivingType.SET_MAX_LEVEL:
                try: MAX_LEVEL = int(chunk)
                except ValueError:
                    print("Max level of the tree must be an integer (got %s)" % chunk)
            elif STATE['receiving'] == ReceivingType.SET_MAX_DEGREE:
                try: MAX_DEGREE = int(chunk)
                except ValueError:
                    print("Max degree of the tree must be an integer (got %s)" % chunk)
            elif STATE['receiving'] == ReceivingType.SET_START_PATH:
                START_PATH = chunk
            STATE['receiving'] = None
        else:
            if chunk == '-l' or chunk == '--level':
                STATE['receiving'] = ReceivingType.SET_MAX_LEVEL
                continue
            if chunk == '-d' or chunk == '--degree':
                STATE['receiving'] = ReceivingType.SET_MAX_DEGREE
                continue
            if chunk == '-p' or chunk == '--path':
                STATE['receiving'] = ReceivingType.SET_START_PATH
                continue
            if chunk == '--stat':
                STATE[ReceivingType.SHOW_STATUS] = True
                continue
            if chunk == '--iterate-all':
                STATE[ReceivingType.ITERATE_ALL] = True
                continue
            print("Unknown command '%s'" % chunk)
            print("[HELP]")
            print("-l --level : set max level of the tree")
            print("-d --degree : set max degree of the tree")
            print("-p --path : set start path")
            print("--stat : show a brief status of items")
            print("--iterate-all : seek all of items even if the limit has exceeded")
            sys.exit()

def draw_list(dir:Path, level=0, tip_list:tuple=(), has_exceeded=False):
    global STATE

    SPACE = "".join([
		("  " if is_tip else "│")
		for is_tip in tip_list
	])
    R = {
        'size': 0,
        'lines': ()
    }
    no_permission = False

    try:
        LIST = [path for path in dir.iterdir()]
        DEGREE = len(LIST)
    except PermissionError:
        no_permission = True

    if no_permission: pass
    else:
        if not has_exceeded and level >= MAX_LEVEL:
            R['lines'] += (SPACE + "└ ...too deep\n",)
            if STATE[ReceivingType.ITERATE_ALL]:
                R['size'] = draw_list(dir, level, (), True)['size']
        else:
            for i, path in enumerate(LIST):
                is_tip = i == DEGREE - 1
                is_long = i >= MAX_DEGREE
                stat = path.stat()

                if not has_exceeded:
                    R['lines'] += (SPACE + ("└" if is_tip or is_long else "├"),)
                if not has_exceeded and is_long:
                    R['lines'] += ("...%d more items\n" % (DEGREE - i),)
                    if STATE.get(ReceivingType.ITERATE_ALL): has_exceeded = True
                    else: break
                if path.is_file():
                    R['size'] += stat.st_size
                    if not has_exceeded:
                        R['lines'] += ("○ %s\n" % Format.of_path(path, stat.st_size),)
                elif path.is_dir():
                    _R = draw_list(path, level + 1, tip_list + (is_tip,))
                    R['size'] += _R['size']
                    if not has_exceeded:
                        R['lines'] += _R['lines']
    R['lines'] = (
        ("ⓧ" if no_permission else "◎")
        + " %s\n" % Format.of_path(dir, R['size'])
    ,) + R['lines']

    return R

class Format:
    def of_size(num, suffix='B'):
        for unit in ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'):
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)
    def of_path(path, size=None):
        global STATE
        if STATE.get(ReceivingType.SHOW_STATUS):
            return "%s [%s]" % (path.name, Format.of_size(size))
        else:
            return path.name

initialize_argv()
print("".join(draw_list(Path(START_PATH).resolve().absolute())['lines']))
