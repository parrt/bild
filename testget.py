import urllib2
import os
import errno

BILD = os.path.expanduser("~/.bild")
LIBCACHE = BILD+"/libs"
JARCACHE = BILD+"/libs/jars"

def modtime(fname):
	try:
		return os.path.getmtime(fname)
	except:
		return 0 # mod date of epoch means ancient  sys.float_info.max  # meaning mod date in future if file not there

def newer(a,b):
	"""
	Return true if a newer than b
	"""
	return modtime(a) < modtime(b)  # smaller is earlier

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

download("http://www.antlr.org/download/antlr-4.2-complete.jar", JARCACHE)