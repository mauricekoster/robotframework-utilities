from suds.client import Client

import logging
import datetime
import sys

import argparse
import re
parser = argparse.ArgumentParser()

parser.add_argument("--url",  help="The Wsdl url",   required=True)
args = parser.parse_args()


if args.url:
	url = args.url
else:
	sys.exit(1)

#print "reading url: %s" % url

client = Client(url ,prettyxml=True)
print client
dump = str(client)

method_line = ""

lines = dump.split('\n')
types = []
after_types=False
after_method=False
for l in lines:
	l = l.strip()

	if after_method:
		method_line = l
		after_method = False

	if after_types:
		if l:
			types.append(l)

	if l.startswith('Method'):
		#print l
		after_types = False
		after_method = True
	if l.startswith('Type'):
		after_types = True
		after_method = False

####
##    Determine methodname and filename
#

r=re.compile("([A-Za-z0-9_]*)\((.*)\)")
a=r.match(method_line)
method_arg=[]
if a:
	methodname = a.group(1)
	method_arg = [a.strip() for a in a.group(2).split(',')]
else:
	methodname = "dummy"
fn = "wrap_" + methodname.lower() + '.txt'

####
##    Constructing user keywords
#

#print "Wsdl: %s" % url
print '-'* 79
print "Method: %s" % method_line

####
##   Generate method invocation
#
# print "Method: %s" % methodname
# print "    Arguments:"
# for a in method_arg:
# 	aa = a.split()
# 	print "        %-20s (%s)" % (aa[1], aa[0])
print

print "Types:"
for l in types:
	lines = []
	args = []

	if ':' in l:
		typename = l.split(":")[1]
		ns = l.split(":")[0]
	else:
		typename = l
		ns ="-"

	# if methodname + "_Reply" == typename:
	# 	continue

	if methodname + "_Request" == typename:
		continue

	print "    %s (%s):" % (typename, ns)

	a=client.factory.resolver.find(l)
	# print a

	print "        attributes:"
	if not a.attributes():
		print "            -"

	for i in a.attributes():
		e = i[0]
		if e.name:
			if e.type:
				print "            %-30s (%s)" % (e.name, e.type[0])
	print "        children:"
	for i in a.children():
		e = i[0]
		if e.name:
			if e.type:
				print "            %-30s (%s)" % (e.name, e.type[0])


	print
