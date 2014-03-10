import os
import subprocess
import errno
import re
import inspect
import sys
import shutil
import urllib2

# evil globals
_ = None
bild_completed = set()  # which *targets* have been built.
BILD = os.path.expanduser("~/.bild")
JARCACHE = os.path.join(BILD,"jars")
CLASSPATH = JARCACHE+"/*" +os.pathsep+ os.environ['CLASSPATH']


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

def rmdir(dir):
	shutil.rmtree(dir, ignore_errors=True)


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

def copytree(src,dst,ignore=None):
	rmdir(dst)
	shutil.copytree(src,dst,ignore=ignore)

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
			#print "a lexer or parser"
			mapping[f] = fullgname + ".java"
		else:
			# must be combined grammar
			#print "a combined"
			mapping[f] = [fullgname + "Parser.java", fullgname + "Lexer.java"]
	return mapping


def newer(a,b):
	"""
	Return true if a newer than b
	"""
	return modtime(a) < modtime(b)  # smaller is earlier

def older(a,b):
	"""
	Return true if a older or same as b
	"""
	return not newer(a,b)


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

def require(target):
	#caller = inspect.currentframe().f_back.f_code.co_name
	if id(target) in bild_completed:	return
	bild_completed.add(id(target))
	target()

def antlr4(srcdir,trgdir=".",cp=CLASSPATH,package=None,version="4.2",args=[]):
	map = antlr_targets(srcdir, trgdir)
	tobuild = stale(map).keys()
	if len(tobuild)==0:
		return
	jarname = "antlr-" + version + "-complete.jar"
	if jarname not in cp:
		download("http://www.antlr.org/download/"+jarname, JARCACHE)
	if package is not None:
		cmd = ["java","-cp",cp,
			   "org.antlr.v4.Tool",
			   "-o",trgdir,
			   "-package",package]+args+tobuild
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

def jar(jarfile, contents=".", srcdir="."):
	trgdir = os.path.dirname(jarfile)
	mkdirs(trgdir)
	if type(contents) == type(""):
		contents = [contents]
	contents_with_C = []
	for f in contents:
		contents_with_C.append("-C")
		contents_with_C.append(srcdir)
		contents_with_C.append(f)
	cmd = ["jar","cmf", "out/META-INF/MANIFEST.MF", jarfile] + contents_with_C
	print cmd
	subprocess.call(cmd)

def go():
	antlr4("src/grammars", "gen/org/foo", package="org.foo")
	javac("src/java", "out")
	javac("gen", "out")
	jar("dist", "app.jar", ["out","resources"])

def download(url,trgdir=".",force=False):
	file_name = url.split('/')[-1]
	mkdirs(trgdir)
	target_name = os.path.join(trgdir,file_name)
	if os.path.exists(target_name) and not force:
		return
	response = urllib2.urlopen(url)
	output = open(target_name,'wb')
	output.write(response.read())
	output.close()

def function(name):
	def afunc():pass
	for f in globals().values():
		if type(f) == type(afunc): print f.__name__
		if type(f) == type(afunc) and f.__name__==name:
			return f
	return None

def processargs(globals):
	if len(sys.argv) == 1:
		target = globals["all"]
	else:
		target = globals[sys.argv[1]]
	if target is not None:
		print "build",target.__name__
		target()
	else:
		print "unknown target:",sys.argv[1]
