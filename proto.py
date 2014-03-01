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

def run(spec):
    print spec
    task = spec[0]
    map = spec[1]
    for src in map:
        print "build",map[src],"from",src,"using",task

def build(*tasks):
    print "tasks",tasks
    for task in tasks:
        for f in task.func_defaults:
            print f
        task()

def init():
    print "init"

def antlr(g, depends=(init,)):
    for d in depends:
        d()
    print "antlr4", g

def javac(f, depends=(antlr,)):
    print "javac", f

mantra       = (antlr, {"Mantra.g4": ["MantraParser.java", "MantraLexer.java"]})
mantrajava   = (javac, {"T.java": "T.class"})

def task_antlr(depends=(init,)):
    for d in depends:
        d()

run(mantra)

