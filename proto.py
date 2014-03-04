import os
import sys
import subprocess
import errno

# evil globals
_ = None
CLASSPATH = os.environ['CLASSPATH']
completed = set()  # which *targets* have been built.


def modtime(fname):
	try:
		return os.path.getmtime(fname)
	except:
		return 0 # mod date of epoch means ancient  sys.float_info.max  # meaning mod date in future if file not there


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


# print files(".", ".xml")
# print files(".")

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


def outofdate(map):  # accept map<string,string> or map<string,list<string>>
	"""
	Return map<string,string-or-list> with files to build as they are out of date
	"""
	out = {}
	for src in map:
		trg = map[src]
		if type(trg) == type([]):
			print "can't handle lists yet"
			out[src] = trg
			continue
		# print src,"->",trg
		# print modtime(src), modtime(trg)
		if modtime(trg) < modtime(src):  # smaller is earlier
			# print "target newer so no build"
			out[src] = trg
	return out

#print javac_targets("/Users/parrt/mantra/code/compiler/src/java", "out")

# out = javac_targets("/Users/parrt/mantra/code/compiler/src/java", "/tmp")

# now we can compare files(dir,".java") with javac_targets(dir,trgdir)
# for file mod

def build(target):
	"""
	Given tuple ({src:target}, task-to-exec, dependencies), build
	targets from src, if not up-to-date, using task-to-exec. First
	make sure dependencies are built.
	"""
	if type(target) is type([]):
		for target in target:
			build(target)
		return
	map = target[0]
	task = target[1]
	dependencies = target[2]
	if id(target) in completed:
		return
	completed.add(id(target))
	print "build", target
	if dependencies is not None:
		if type(dependencies) is type([]):
			for d in dependencies:
				build(d)
		else:
			build(dependencies)
	if map is not None:
		tobuild = outofdate(map)
		if len(tobuild)==0:
			print target[1],"up to date"
		for src in tobuild:
			print "build", map[src], "from", src  #, "using", task, "depends on", dependencies
			task(src,map[src])
	else:
		task()  # no src -> target, just exec


def task_init():
	print "init"


def antlr(src,trg):
	print "antlr4",src


def javac(src, trg, cp=CLASSPATH, outdir=".", args=[]):
	outdir = uniformpath(outdir)
	mkdirs(outdir)
	cmd = ["javac", "-d", outdir, "-cp", cp] + args + [src]
	print cmd
	subprocess.call(cmd)


def jar(dir, jarfile, files):
	mkdirs(dir)
	cmd = ["jar","cf", os.path.join(dir,jarfile)] + files
	print cmd
	subprocess.call(cmd)

# target defs are tuples: ({src:target}, task-to-exec, dependencies)
init = (_, task_init, _)
mantra = ({"Mantra.g4": ["MantraParser.java", "MantraLexer.java"]}, antlr, init)
compilesrc = (javac_targets("src/java", "out"),
			  lambda src,trg: javac(src,trg,outdir="out"),
			  [mantra, init])
mkjar = (_, lambda : jar(dir="dist",jarfile="app.jar",files=["resources", "out"]), compilesrc)

all = [init, mantra]  # can be list of targets

build(mkjar)


class JavaProj:
	def __init__(self, name):
		self.name = name
		return

	def java(self, *srcdirs):
		return

	def resources(self, *resdirs):
		return

	def libs(self, *libs):
		return

	def artifacts(self, *includes):
		return


myproj = JavaProj("myproj")
myproj.java("src/java", "gen")
myproj.resources("resources")
myproj.libs("/usr/local/lib/antlr-4.2-complete.jar")
