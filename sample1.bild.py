from bild import *

# can set as you like:
# CLASSPATH = ...

projversion = 1.0

def T(): # there is a T.g4 grammar in src/grammars
	antlr4("src/grammars", "gen/org/foo", package="org.foo")

def compile():
	require(T)
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

"""
manifest {
        attributes("Implementation-Title": "Gradle",
        "Implementation-Version": version)
    }
"""

processargs(globals()) # if you want cmd-line arg processing. Or, just call your target