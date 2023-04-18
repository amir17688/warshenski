import re
import readline
from functools import wraps
import shlex

from color import prnt, VIOLET, RED


class CmdError(Exception):
    pass


def command(func):
    @wraps(func)
    def cmd_trycatch(self, arg):
        args = shlex.split(arg, comments=True)
        try:
            func(self, args)
        except CmdError as e:
            prnt("Error: {}.".format(str(e)), RED)
            prnt("Command details:", RED)
            prnt("\tCommand:\n\t\t->\"{}\"".format(pure_cmd_name(func)), RED)
            prnt("\tArgument string:\n\t\t->\"{}\"".format(arg), RED)
    return cmd_trycatch


def state(func):
    @wraps(func)
    def set_state(self, args):
        self.state.set_state(func(self, args))

    return set_state


def emptystate(func):
    @wraps(func)
    def set_state(self, args):
        self.state.clear_state()
        func(self, args)

    return set_state


class arglen:
    def __init__(self, min, max=None):
        self.min = min
        if not max:
            self.max = self.min
        else:
            self.max = max

    def __call__(self, func):
        @wraps(func)
        def arglen_check(func_self, args):
            if self.min <= len(args) and len(args) <= self.max:
                return func(func_self, args)
            else:
                raise CmdError(
                        "The '{}' command takes between [{}, {}] args"
                        .format(
                            func.__name__.split('_')[1], self.min, self.max
                            )
                        )

        return arglen_check


def _get_pat_and_hint(arg):
    inject_base_pat = '%{}:["]?({})["]?'
    hint_base = '%{}'

    if '%p:' in arg:
        pat = inject_base_pat.format('p', '\d+')
        hint = hint_base.format('p')
    elif '%s:' in arg:
        pat = inject_base_pat.format('s', '.+')
        hint = hint_base.format('s')
    elif '%:' in arg:
        pat = inject_base_pat.format('', '.+')
        hint = hint_base.format('')
    elif '%c:' in arg:
        pat = inject_base_pat.format('c', '')
        hint = hint_base.format('c')
    elif '%cp:' in arg:
        pat = inject_base_pat.format('cp', '\d+')
        hint = hint_base.format('cp')
    else:
        pat, hint = None, None

    return pat, hint


def _inject_id(self, args, i, pat, hint):
    res = re.compile(pat).search(args[i])
    if not res:
        raise CmdError("Invalid substitution argument")
    val = res.group(1)
    inject_id = str(self.state.fetch(val, hint=hint).obj_id)
    args[i] = re.sub(pat, inject_id, args[i])


def inject(func):
    @wraps(func)
    def inject_arg(self, args):
        for i in range(len(args)):
            arg = args[i]
            pat, hint = _get_pat_and_hint(arg)
            if not pat and not hint:
                continue

            _inject_id(self, args, i, pat, hint)

        func(self, args)

    return inject_arg


class restrict:
    def __init__(self, subcmds):
        self.subcmds = subcmds

    def __call__(self, func):
        @wraps(func)
        def restrict_subcmds(func_self, args):
            if args[0] in self.subcmds:
                func(func_self, args)
            else:
                err_msg = "Sub command must be one of: {}".format(self.subcmds)
                raise CmdError(err_msg)

        return restrict_subcmds


def readline_inject(args):
    # Inject into readline to use the injected command.
    history_len = readline.get_current_history_length()
    last_item = readline.get_history_item(history_len)
    cmd = ' '.join([last_item.split()[0]] + args)
    readline.replace_history_item(history_len-1, cmd)


def print_listing(items, pos):
    for offset, item in enumerate(items):
        prnt(pos+offset, '. ', item, VIOLET, None, None)
    return pos + len(items)


def pure_cmd_name(cmd_func):
    return cmd_func.__name__[len('do_'):]
