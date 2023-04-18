import sys
import os
import contextlib

def IO_redirection(cmd):
    """
    Redirect input/output based characters < > >> in the command.
    < will be redirecting input, > will be output and >> is output append
    """
    #check for input redirection first
    if("<" in cmd):
        SetUpInputRedirect(cmd)

    if(">" in cmd):
        SetUpOutputRedirect(cmd)

    if(">>" in cmd):
        SetUpAppendRedirect(cmd)

def SetUpInputRedirect(cmd):
    import pdb; pdb.set_trace()
    pass

def SetUpOutputRedirect(cmd):
    i = cmd.index(">")
    sys.stdout = open(cmd[i + 1], "w")
    del cmd[i + 1]
    del cmd[i]
    print("this is a test")

def SetUpAppendRedirect(cmd):
    import pdb; pdb.set_trace()
    pass
