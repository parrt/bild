from bild import *

def T(): # there is a T.g4 grammar in src/grammars
	antlr("src/grammars", "gen/org/foo", package="org.foo")

def compile():
	require(T())
	javac("src/java", "out")
	javac("gen", "out")

def mkjar():
	require(compile())
	jar("dist", "app.jar", ["out","resources"])

def all():
	mkjar()

def clean():
	rmdir("out")
	rmdir("gen")

def clean_all():
	require(clean())
	rmdir("dist")

build(globals()) # if you want cmd-line arg processing. Or, just call your target
