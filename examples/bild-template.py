#!/usr/bin/env python

"""
Template bild.py file that has the two key elements:
    1. bootstrapping code to download bilder.py lib
    2. processargs(globals()) call to allow target names as args to python process
"""
# bootstrap by downloading bilder.py if not found
import urllib
import os

if not os.path.exists("bilder.py"):
    print "bootstrapping; downloading bilder.py"
    urllib.urlretrieve(
        "https://raw.githubusercontent.com/parrt/bild/master/src/python/bilder.py",
        "bilder.py")

# assumes bilder.py is in current directory
from bilder import *

def mytarget():
    # python code to build mytarget
    # ...

processargs(globals())  # if you want cmd-line arg processing; ./bild.py targetname
# Or, just call your target in main like this:
# mytarget()
