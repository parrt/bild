import os

# Copyright (c) 2007-2008,
#   Bill McCloskey    <bill.mccloskey@gmail.com>
# All rights reserved.
# BSD license
# Borrow from http://web.archive.org/web/20090117001916/http://www.cs.berkeley.edu/~billm/memoize.py
def modtime(fname):
    """Return the modification time of a given filename, or None
    if there is a problem. (i.e: file doesn't exist.)
    """
    try:
        if os.path.isdir(fname):
            return 1
        else:
            return os.path.getmtime(fname)
    except:
        return None

def build(*specs):
    for spec in specs:
        print spec
        task = spec[0]
        map = spec[1]
        for src in map:
            print "build",map[src],"from",src,"using",task

def antlr(g):
    print "antlr4", g

def javac(f):
    print "javac", f

mantra       = (antlr, {"Mantra.g4":["MantraParser.java", "MantraLexer.java"]})
mantrajava   = (javac, {"T.java":"T.class"})

build(mantra, mantrajava)

