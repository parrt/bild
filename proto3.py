import bild
import sys
def antlr():
	bild.antlr("src/grammars", "gen/org/foo", package="org.foo")

def compile():
	bild.require(antlr())
	bild.javac("src/java", "out")
	bild.javac("gen", "out")

def jar():
	bild.require(compile())
	bild.jar("dist", "app.jar", ["out","resources"])

def all():
	bild.require(compile())
	jar()

def clean():
	bild.rmdir("out")
	bild.rmdir("gen")

def clean_all():
	bild.require(clean())
	bild.rmdir("dist")

#bild.build(globals()) # if you want cmd-line arg processing. Or, just call your target

all()