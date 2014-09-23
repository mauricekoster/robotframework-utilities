from suds.client import Client
import datetime
import sys
import argparse
import re
parser = argparse.ArgumentParser()

parser.add_argument("--url",  help="The Wsdl url",   required=True)
parser.add_argument("--keyword-prefix", "-k", help="Keyword prefix",  dest='kw')
parser.add_argument("--use-variable", "-u", help="Use variable instead of url",  dest='usevar', action="store_true")
args = parser.parse_args()


if args.url:
	url = args.url
else:
	sys.exit(1)

if args.kw:
	keyword_prefix = args.kw
else:
	keyword_prefix = "Create"



print "reading url: %s" % url

####
##    Processing
#

client = Client(url, prettyxml=True)
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


if args.usevar:
	wsdl = "${WS_%s_WSDL}" % methodname.upper()
else:
	wsdl = url

####
##    Constructing user keywords
#

output = []
output.append("*** Settings ***")
output.append("Documentation     Wsdl: %s" % url)
output.append("Documentation     Method: %s" % method_line)
output.append("Library           SudsLibrary")
output.append("")
output.append("*** Keywords ***")

for l in types:
	lines = []
	args = []



	if ':' in l:
		typename = l.split(":")[1]
	else:
		typename = l

	if methodname + "_Reply" == typename:
		continue

	if methodname + "_Request" == typename:
		continue

	a=client.factory.resolver.find(l)
	for i in a.attributes():
		e = i[0]
		if e.name:
			if e.type:
				varname = "${%s}" % e.name

				line = "    Set Wsdl Object Attribute    ${wsdlobject}    _%s    %s" % (e.name, varname.lower())
				lines.append(line)
				args.append(varname.lower())

	for i in a.children():
		#print i
		e = i[0]



		if e.name:
			if e.type:
				varname = "${%s}" % e.name

				line = "    Set Wsdl Object Attribute    ${wsdlobject}    %s    %s" % (e.name, varname.lower())
				lines.append(line)
				args.append(varname.lower())

	output.append("%s %s" % (keyword_prefix, typename))
	output.append("    [Arguments]    " + '    '.join(args))
	output.append("    ${wsdlobject}=    Create Wsdl Object    %s" % l)
	output.extend(lines)
	output.append("    [Return]    ${wsdlobject}")
	output.append("")

####
##   Generate method invocation
#
output.append("Invoke %s" % methodname )
ma = '   '.join(['${' + a.split()[1].lower() +'}' for a in method_arg])
output.append( "    [Arguments]   %s" % ma )
output.append( "    ${result}=    Call Soap Method    %s   %s" % (methodname, ma) )
output.append( "    [Return]   ${result}" )
output.append("")

# ... and when expecting fault
output.append("Invoke %s Expecting Fault" % methodname )
ma = '   '.join(['${' + a.split()[1].lower() +'}' for a in method_arg])
output.append( "    [Arguments]   %s" % ma )
output.append( "    ${result}=    Call Soap Method Expecting Fault   %s   %s" % (methodname, ma) )
output.append( "    [Return]   ${result}" )
output.append("")

####
##   Generate create and switch soap client invocation
#
output.append("Switch Soap Client %s" % methodname )
output.append( "    Switch Soap Client    %s" % ("ws" + methodname) )
output.append("")
output.append("Create Soap Client %s" % methodname )
output.append( "    Create Soap Client    %s    %s" % (wsdl, "ws" + methodname) )
output.append("")
####
##	  Writing to output file
#

with open(fn, "w") as f:
	for o in output:
		f.write( "%s\n" % o)

print "File created: %s" % fn
