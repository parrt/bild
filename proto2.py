from bild import *

####################################################################

def target_antlr():
	antlr("src/grammars", "gen/org/foo", package="org.foo")

def target_compile():
	require(target_antlr())
	javac("src/java", "out")
	javac("gen", "out")

def target_jar():
	require(target_compile())
	jar("dist", "app.jar", ["out","resources"])

def target_all():
	require(target_compile())
	target_jar()

def target_clean():
	rmdir("out")
	rmdir("gen")

def target_clean_all():
	require(target_clean())
	rmdir("dist")

build(globals()) # if you want cmd-line arg processing. Or, just call your target
