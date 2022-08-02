######################################################################
#   File: platform.py
#
#   Description:
#       Determines the platform (OS) used by the system to ensure 
#       that the right keyboard shortcuts are used and to determine
#       the expected location of diffmerge.
#
#   Included functions:
#       - is_mac(), is_win(), is_linux(), accelerator_string(),
#         diffmerge_exec()
#
######################################################################

import sys

def is_mac():
    """Returns true if Test Center is run on a Mac"""
    return sys.platform=="darwin"

def is_win():
    """Returns true if Test Center is run on a Windows computer"""
    return sys.platform[:3] == "win"

def is_linux():
    """Returns true if Test Center is run on a Linux computer"""
    return sys.platform[:5] == "linux"

def accelerator_string():
    """ Determines which accelerator string (Command
    or CTRL) should be displayed and used as a keyboard
    shortcut.
    """
    if is_mac():
        return "Command"
    else:
        return "Ctrl"

def diffmerge_exec():
    """ Sets up the location of diffmerge on the host machine.
    Unfortunately hardcoded.
    """  
    # application location differs from platform to platform 
    osx_diffmerge_exec = "/Applications/DiffMerge/DiffMerge.app/Contents/MacOS/DiffMerge"
    win_diffmerge_exec = "C:/Program Files (x86)/SourceGear/DiffMerge/DiffMerge.exe"
    linux_diffmerge_exec = "diffmerge"

    if is_mac():
        return osx_diffmerge_exec

    if is_win():
        return win_diffmerge_exec

    return linux_diffmerge_exec