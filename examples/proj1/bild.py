#!/usr/bin/env python
# bootstrap by downloading bilder.py if not found
import urllib

if not os.path.exists("bilder.py"):
    print "bootstrapping; downloading bilder.py"
    urllib.urlretrieve(
        "https://raw.githubusercontent.com/parrt/bild/master/src/python/bilder.py",
        "bilder.py")

# assumes bilder.py is in current directory
from bilder import *

projversion = 1.0


def parser():  # there is a T.g4 grammar in src/grammars
    antlr4("src/grammars", "gen", package="org.foo")


def compile():
    require(parser)
    javac("src/java", "out")
    javac("gen", "out")


def mkjar():
    require(compile)
    copytree(src="resources", dst="out/resources")
    manifest = """Version: %s
Main-Class: org.foo.Blort
""" % projversion
    jar("dist/app.jar", srcdir="out", manifest=manifest)


def all():
    mkjar()


def clean():
    rmdir("out")
    rmdir("gen")


def clean_all():
    require(clean)
    rmdir("dist")


processargs(globals())  # if you want cmd-line arg processing. Or, just call your target
