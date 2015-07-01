import argparse

_arg_parser = argparse.ArgumentParser(
    prog='pisak',
    description='PISAK - Polish Integrating System of Alternative Communication',
    epilog='This program is licensed under the terms of the GNU GPL version 3.')

_arg_parser.add_argument('-d', '--debug', action='store_true', help='run in debug mode (enables extensive logging to console and to the log file)')
_arg_parser.add_argument('-s', '--skin', default='default', help='set skin')
_arg_parser.add_argument('args', nargs=argparse.REMAINDER, help='arguments passed to applications')

_args = None


def get_args():
    global _args
    if _args is None:
        _args, _ = _arg_parser.parse_known_args()
    return _args

