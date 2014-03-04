import os
import subprocess
import errno
import re
import inspect
import sys

# evil globals
_ = None
CLASSPATH = os.environ['CLASSPATH']
completed = set()  # which *targets* have been built.


def modtime(fname):
	try:
		return os.path.getmtime(fname)
	except:
		return 0  # mod date of epoch means ancient  sys.float_info.max  # meaning mod date in future if file not there


def uniformpath(dir):
	dir = os.path.expanduser(dir)  # ~parrt -> /Users/parrt on unix
	dir = os.path.abspath(dir)  # expand relative dirs
	return dir


def mkdirs(path):
	"""
	From: http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
	"""
	try:
		os.makedirs(path)
	except OSError as exc:  # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise


def files(dir, suffix=None):
	"""
	Return list<string> all files in subtree dir, optionally matching
	a suffix like ".java"
	"""
	dir = uniformpath(dir)
	matching_files = []
	for root, subFolders, files in os.walk(dir):
		for f in files:
			fullname = os.path.join(root, f)
			if suffix is not None:
				ext = os.path.splitext(fullname)[1]
				if ext == suffix:
					matching_files.append(fullname)
			else:
				matching_files.append(fullname)
	return matching_files


def replsuffix(files, suffix):
	"""
	Return list<string> all files with their .suffix replaced
	"""
	outfiles = []
	if suffix is None: return
	for f in files:
		fname, ext = os.path.splitext(f)
		newfname = fname + suffix
		outfiles.append(newfname)
	return outfiles


def javac_targets(srcdir, trgdir):
	"""
	Return a map<string,string> of files javac would create given a subdir of java
	files and a target dir. E.g.,
	javac_targets("/Users/parrt/mantra/code/compiler/src/java", "out")
	generates
		{".../src/java/mantra/Tool.java":"out/mantra/Tool.class", ...}
	"""
	srcdir = uniformpath(srcdir)
	trgdir = uniformpath(trgdir)
	mapping = {}
	javafiles = files(srcdir, ".java")
	classfiles = replsuffix(javafiles, ".class")
	classfiles = [f.replace(srcdir, trgdir) for f in classfiles]  # shift to trg dir
	for i in range(len(javafiles)):
		mapping[javafiles[i]] = classfiles[i]
	return mapping


def grep(file, regex):
	matches = []
	with open(file) as f:
		contents = f.read()
		m = re.search(regex, contents)
		if m:
			matches.append(m.group())
	return matches


def antlr_targets(srcdir, trgdir):
	"""
	Return a map<string,string> of files antlr would create given a subdir of grammars
	files and a target dir. E.g.,
	javac_targets("/Users/parrt/mantra/code/compiler/src/java", "out")
	generates
		{".../src/grammars/foo/T.g4":["out/foo/TParser.java", ...}
	"""
	srcdir = uniformpath(srcdir)
	trgdir = uniformpath(trgdir)
	mapping = {}
	gfiles = files(srcdir, ".g4")
	for f in gfiles:
		fdir, fsuffix = os.path.splitext(f)
		gname = os.path.basename(fdir)
		fullgname = os.path.join(trgdir, gname)
		lexer = grep(f, r"lexer\s+grammar")
		parser = grep(f, r"parser\s+grammar")
		if len(lexer) > 0 or len(parser) > 0:
			print "a lexer or parser"
			mapping[f] = fullgname + ".java"
		else:
			# must be combined grammar
			print "a combined"
			mapping[f] = [fullgname + "Parser.java", fullgname + "Lexer.java"]
	return mapping


def stale(map):  # accept map<string,string> or map<string,list<string>>
	"""
	Return map<string,string-or-list> with files to build as they are out of date
	"""
	out = {}
	for src in map:
		trg = map[src]
		isstale = False
		if type(trg) == type([]):
			for t in trg:
				if modtime(t) < modtime(src):  # smaller is earlier
					isstale = True
					break
		else:
			# print src,"->",trg
			# print modtime(src), modtime(trg)
			if modtime(trg) < modtime(src):  # smaller is earlier
				# print "target newer so no build"
				isstale = True
		if isstale:
			out[src] = trg
	return out


def done():
	# caller_index = 1
	# name_index = 3
	#caller = inspect.stack()[caller_index][name_index]
	caller = inspect.currentframe().f_back.f_code.co_name
	if caller in completed:
		return True
	completed.add(caller)
	return False

def antlr(srcdir,trgdir=".",package=None,args=[]):
	print "antlr4",srcdir,trgdir
	map = antlr_targets(srcdir, trgdir)
	tobuild = stale(map).keys()
	print "build",stale(map)
	if len(tobuild)==0:
		return
	if package is not None:
		cmd = ["java","org.antlr.v4.Tool","-o",trgdir,"-package",package]+args+tobuild
	else:
		cmd = ["java","org.antlr.v4.Tool","-o",trgdir]+args+tobuild
	print cmd
	subprocess.call(cmd)


def javac(srcdir, trgdir=".", cp=None, args=[]):
	srcdir = uniformpath(srcdir)
	trgdir = uniformpath(trgdir)
	mkdirs(trgdir)
	map = javac_targets(srcdir, trgdir)
	tobuild = stale(map).keys()
	# print "build",stale(map)
	if len(tobuild)==0:
		return
	if cp is not None:
		cp = cp + os.pathsep + trgdir + os.pathsep + CLASSPATH
	else:
		cp = trgdir + os.pathsep + CLASSPATH
	cmd = ["javac", "-sourcepath", srcdir, "-d", trgdir, "-cp", cp] + args + tobuild
	print cmd
	subprocess.call(cmd)

def jar(dir, jarfile, files):
	mkdirs(dir)
	cmd = ["jar","cf", os.path.join(dir,jarfile)] + files
	print cmd
	subprocess.call(cmd)

####################################################################

def target_init():
	if done(): return
	print "init"
	return


def target_antlr():
	if done(): return
	target_init()
	antlr("src/grammars", "gen/org/foo", package="org.foo")
	print "antlr"
	return


def target_compile():
	if done(): return
	target_init()
	target_antlr()
	print "compile"
	javac("src/java", "out")
	javac("gen", "out")
	return

def target_all():
	target_compile()
	return

if len(sys.argv) == 1:
	target_all()
else:
	if sys.argv[1]=="all":
		target_all()
	elif sys.argv[1]=="compile":
		target_compile()
	elif sys.argv[1]=="antlr":
		target_antlr()
	else:
		print "unknown target:",sys.argv[1]
