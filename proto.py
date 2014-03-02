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

_ = None

completed = set() # which *targets* have been built.

def run(spec):
	if type(spec) is type([]):
		for target in spec:
			run(target)
		return
	task = spec[0]
	map = spec[1]
	dependencies = spec[2]
	if id(spec) in completed:
		return
	completed.add(id(spec))
	print "run", spec
	if dependencies is not None:
		if type(dependencies) is type([]):
			for d in dependencies:
				run(d)
		else:
			run(dependencies)
	if map is not None:
		for src in map:
			print "build", map[src], "from", src, "using", task, "depends on", dependencies
			task(src)
	else:
		task() # no src -> target, just exec

# def buildtasks(*tasks):
# 	print "tasks", tasks
# 	for task in tasks:
# 		for f in task.func_defaults:
# 			print f
# 		task()

def task_init():
	print "init"

def antlr(g):
	print "antlr4", g

def javac(f):
	print "javac", f


# target defs are tuples: (task-to-exec, {src:target}, dependencies)
init = (task_init,_,_)
mantra = (antlr, {"Mantra.g4": ["MantraParser.java", "MantraLexer.java"]}, init)
mantrajava = (javac, {"MantraParser.java": "MantraParser.class"}, [mantra,init])
all = [init,mantra] # can be list of targets

def task_antlr(depends=(init,)):
	for d in depends:
		d()

run(all)

