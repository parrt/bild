import os
import subprocess
import errno
import re
import sys
import shutil
import urllib2
import glob
import string
from distutils import dir_util
from distutils import file_util
import zipfile

# evil globals
_ = None
bild_completed = set()  # which *targets* have been built.
BILD = os.path.expanduser("~/.bild")
JARCACHE = os.path.join(BILD, "jars")
#CLASSPATH = JARCACHE + "/*" + os.pathsep + os.environ['CLASSPATH']

def findjdks_win():
	return {}

def findjdks_linux():
	"""
	CentOS: /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.55.x86_64/jre/bin/java
					/usr/java/jdk1.7.0_51
	ubuntu: /usr/lib/jvm/java-6-openjdk/ for OpenJDK
					/usr/lib/jvm/* for Oracle JDK
	"""
	versions = {}
	for jdk in glob.glob("/usr/lib/jvm/*") + glob.glob("/usr/java/*"):
			name = os.path.basename(jdk)
			if name.startswith("java-1.6") or name.startswith("jdk1.6"):
					versions["1.6"] = jdk
			if name.startswith("java-1.7") or name.startswith("jdk1.7"):
					versions["1.7"] = jdk
			if name.startswith("java-1.8") or name.startswith("jdk1.8"):
					versions["1.8"] = jdk
	return versions

def findjdks_mac():
	"""find Java installations on a mac"""
	versions = {}
	for jdk in glob.glob("/Library/Java/JavaVirtualMachines/*"):
		name = os.path.basename(jdk)
		if name.startswith("1.6."):
			versions["1.6"] = jdk+"/Contents/Home"
		elif name.startswith("jdk1.7."):
			versions["1.7"] = jdk+"/Contents/Home"
		elif name.startswith("jdk1.8."):
			versions["1.8"] = jdk+"/Contents/Home"
	return versions

def findjdks():
	if sys.platform == 'win32':
		return findjdks_win()
	if sys.platform == 'darwin':
		return findjdks_mac()
	if sys.platform == 'linux2':
		return findjdks_linux()

jdk = findjdks()

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


def filelist(pathspec):
	files = []
	for f in glob.glob(pathspec):
		if os.path.getsize(f) > 0:
			files.append(f)
	return files


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

def copytree(src, dst, ignore=None):
	dir_util.copy_tree(src, dst, preserve_mode=True)

def copyfile(src, dst):
	file_util.copy_file(src, dst, preserve_mode=True)

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


def antlr3_targets(srcdir, trgdir, package=None):
	"""
	Return a map<string,string> of files antlr3 would create given a subdir of grammars
	files and a target dir. E.g.,
	antlr3_targets("tool/src/org/antlr/v4/codegen", "gen")
	gives:
	{'/Volumes/SSD2/Users/parrt/antlr/code/antlr4/tool/src/org/antlr/v4/codegen/SourceGenTriggers.g':
	 '/Volumes/SSD2/Users/parrt/antlr/code/antlr4/gen/SourceGenTriggers.java'}
	"""
	srcdir = uniformpath(srcdir)
	if package is not None:
		package = re.sub('[.]', '/', package)
		trgdir = uniformpath(os.path.join(trgdir,package))
	else:
		trgdir = uniformpath(trgdir)
	mapping = {}
	gfiles = files(srcdir, ".g")
	for f in gfiles:
		fdir, fsuffix = os.path.splitext(f)
		gname = os.path.basename(fdir)
		fullgname = os.path.join(trgdir, gname)
		lexer = grep(f, r"lexer\s+grammar")
		parser = grep(f, r"parser\s+grammar")
		tree = grep(f, r"tree\s+grammar")
		if len(lexer) > 0 or len(parser) > 0 or len(tree) > 0:
			# print "a lexer or parser or tree parser"
			mapping[f] = fullgname + ".java"
		else:
			# must be combined grammar
			# print "a combined"
			mapping[f] = [fullgname + "Parser.java", fullgname + "Lexer.java"]
	return mapping


def antlr4_targets(srcdir, trgdir, package=None):
	"""
	Return a map<string,string> of files antlr4 would create given a subdir of grammars
	files and a target dir. E.g.,
	antlr4_targets("tests", "gen")
	gives:
	{'/Volumes/SSD2/Users/parrt/github/bild/tests/sample1/src/grammars/org/foo/T.g4':
	  ['/Volumes/SSD2/Users/parrt/github/bild/gen/TParser.java',
	   '/Volumes/SSD2/Users/parrt/github/bild/gen/TLexer.java']
	}
	"""
	srcdir = uniformpath(srcdir)
	if package is not None:
		package = re.sub('[.]', '/', package)
		trgdir = uniformpath(os.path.join(trgdir,package))
	else:
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
			# print "a lexer or parser"
			mapping[f] = fullgname + ".java"
		else:
			# must be combined grammar
			# print "a combined"
			mapping[f] = [fullgname + "Parser.java", fullgname + "Lexer.java"]
	return mapping


def newer(a, b):
	"""
	Return true if a newer than b
	"""
	return modtime(a) < modtime(b)  # smaller is earlier


def older(a, b):
	"""
	Return true if a older or same as b
	"""
	return not newer(a, b)


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
				# print src,"->",t
				# print modtime(src), modtime(t)
				if is_stale(src,t):
					isstale = True
					break
		else:
			# print src,"->",trg
			# print modtime(src), modtime(trg)
			if is_stale(src,trg):
				# print "target newer so no build"
				isstale = True
		if isstale:
			out[src] = trg
	return out

def is_stale(src,trg):
	return modtime(trg) < modtime(src);  # smaller is earlier


def require(target):
	# caller = inspect.currentframe().f_back.f_code.co_name
	if id(target) in bild_completed:    return
	bild_completed.add(id(target))
	target()


def antlr3(srcdir, trgdir=".", package=None, version="3.5.1", args=[]):
	map = antlr3_targets(srcdir, trgdir, package)
	tobuild = stale(map).keys()
	if len(tobuild) == 0:
		return
	jarname = "antlr-" + version + "-complete.jar"
	#if jarname not in filelist(JARCACHE):
	download("http://www.antlr3.org/download/" + jarname, JARCACHE)
	if package is not None:
		packageAsDir = re.sub('[.]', '/', package)
		cmd = ["java", "-cp", os.path.join(JARCACHE, jarname),
			   "org.antlr.Tool",
			   "-o", os.path.join(trgdir, packageAsDir)] + args + tobuild
	else:
		cmd = ["java", "org.antlr.Tool", "-o", trgdir] + args + tobuild
	print cmd
	subprocess.call(cmd)


def antlr4(srcdir, trgdir=".", package=None, version="4.3", args=[]):
	map = antlr4_targets(srcdir, trgdir, package)
	tobuild = stale(map).keys()
	if len(tobuild) == 0:
		return
	jarname = "antlr-" + version + "-complete.jar"
	# if jarname not in filelist(JARCACHE):
	download("http://www.antlr.org/download/" + jarname, JARCACHE)
	if package is not None:
		packageAsDir = re.sub('[.]', '/', package)
		cmd = ["java", "-cp", os.path.join(JARCACHE, jarname),
			   "org.antlr.v4.Tool",
			   "-o", os.path.join(trgdir, packageAsDir),
			   "-package", package] + args + tobuild
	else:
		cmd = ["java", "org.antlr.v4.Tool", "-o", trgdir] + args + tobuild
	print string.join(cmd, " ")
	subprocess.call(cmd)


def javac(srcdir, trgdir=".", cp=None, version=None, args=[]):
	srcdir = uniformpath(srcdir)
	trgdir = uniformpath(trgdir)
	mkdirs(trgdir)
	map = javac_targets(srcdir, trgdir)
	tobuild = stale(map).keys()
	# print "build",stale(map)
	if len(tobuild) == 0:
		return
	if cp is None:
		cp = trgdir + os.pathsep + JARCACHE + "/*"
	# cmd = ["javac", "-sourcepath", srcdir, "-d", trgdir, "-cp", cp] + args + tobuild
	javac="javac"
	if version is not None:
		javac = os.path.join(jdk[version],"bin/javac")
	cmd = [javac, "-d", trgdir, "-cp", cp] + args + tobuild
	print string.join(cmd, " ")
	subprocess.call(cmd)


def jar(jarfile, inputfiles=".", srcdir=".", manifest=None):
	trgdir = os.path.dirname(jarfile)
	mkdirs(trgdir)
	if type(inputfiles) == type(""):
		inputfiles = [inputfiles]
	contents_with_C = []
	for f in inputfiles:
		contents_with_C.append("-C")
		contents_with_C.append(srcdir)
		contents_with_C.append(f)
	# write manifest
	metadir = os.path.join(srcdir, "META-INF")
	mkdirs(metadir)
	with open(os.path.join(metadir, "MANIFEST.MF"), "w") as mf:
		mf.write(manifest)
	mfile = os.path.join(srcdir, "META-INF/MANIFEST.MF")
	cmd = ["jar", "cmf", mfile, jarfile] + contents_with_C
	print cmd
	subprocess.call(cmd)

def unjar(jarfile, trgdir="."):
	jar = zipfile.ZipFile(jarfile)
	jar.extractall(path=trgdir)

def download(url, trgdir=".", force=False):
	file_name = url.split('/')[-1]
	mkdirs(trgdir)
	target_name = os.path.join(trgdir, file_name)
	if os.path.exists(target_name) and not force:
		return
	try:
		response = urllib2.urlopen(url)
	except urllib2.HTTPError:
		sys.stderr.write("can't download %s\n" % url)
	else:
		output = open(target_name, 'wb')
		output.write(response.read())
		output.close()


def function(name):
	def afunc():
		pass

	for f in globals().values():
		if type(f) == type(afunc): print f.__name__
		if type(f) == type(afunc) and f.__name__ == name:
			return f
	return None


def processargs(globals):
	if len(sys.argv) == 1:
		target = globals["all"]
	else:
		target = globals[sys.argv[1]]
	if target is not None:
		print "build", target.__name__
		target()
	else:
		sys.stderr.write("unknown target: %s\n" % sys.argv[1])
