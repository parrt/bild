import os


def modtime(fname):
    try:
        return os.path.getmtime(fname)
    except:
        return None


def files(dir, suffix=None):
    """
    Return list<string> all files in subtree dir, optionally matching
    a suffix like ".java"
    """
    dir = os.path.expanduser(dir)  # ~parrt -> /Users/parrt on unix
    dir = os.path.abspath(dir)  # expand relative dirs
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
    mapping = {}
    javafiles = files(srcdir, ".java")
    classfiles = replsuffix(javafiles, ".class")
    classfiles = [f.replace(srcdir, trgdir) for f in classfiles]  # shift to trg dir
    for i in range(len(javafiles)):
        mapping[javafiles[i]] = classfiles[i]
    return mapping

#print javac_targets("/Users/parrt/mantra/code/compiler/src/java", "out")

# out = javac_targets("/Users/parrt/mantra/code/compiler/src/java", "/tmp")
out = javac_targets("../../antlr/code/antlr3/tool/src/main/java", "/tmp")
for src in out:
    trg = out[src]
    print modtime(src), modtime(trg)

# now we can compare files(dir,".java") with javac_targets(dir,trgdir)
# for file mod

_ = None

completed = set()  # which *targets* have been built.


def build(target):
    if type(target) is type([]):
        for target in target:
            build(target)
        return
    task = target[0]
    map = target[1]
    dependencies = target[2]
    if id(target) in completed:
        return
    completed.add(id(target))
    print "run", target
    if dependencies is not None:
        if type(dependencies) is type([]):
            for d in dependencies:
                build(d)
        else:
            build(dependencies)
    if map is not None:
        for src in map:
            print "build", map[src], "from", src, "using", task, "depends on", dependencies
            task(src)
    else:
        task()  # no src -> target, just exec


def task_init():
    print "init"


def antlr(g):
    print "antlr4", g


def javac(f, args=""):
    # if file or dir
    print "javac", args, f


def jar(files):
    print files

# target defs are tuples: (task-to-exec, {src:target}, dependencies)
init = (task_init, _, _)
mantra = (antlr, {"Mantra.g4": ["MantraParser.java", "MantraLexer.java"]}, init)
mantrajava = (lambda x: javac(x, "-g"), {"MantraParser.java": "MantraParser.class"}, [mantra, init])
compilesrc = (javac, {"src": "out"}, [mantra, init])  #dirs
mkjar = (jar, {"app.jar": ["resources", "out"]}, compilesrc)
# args to task? nah, make new task. can have generic javac then make myjavac that
# invokes javac with correct args. Too bad lambdas can only be expressions.
# actually, that's enough. can call task with args!
mkjar2 = (lambda x: jar(x), {"app.jar": ["resources", "out"]}, compilesrc)

all = [init, mantra]  # can be list of targets

build(mantrajava)

