#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import sys
import os.path
from collections import OrderedDict

VERBOSE = True

def eprint(*args, **kwargs):
    print(*args, file = sys.stderr, **kwargs)

if __name__ == "__main__":
	if len(sys.argv) != 3:
		eprint("Usage: {0} <reference> <input>".format(sys.argv[0]))
		exit(1)

	REFERENCE = sys.argv[1]
	INPUT = sys.argv[2]

	RefFP = open(REFERENCE, "rb")
	RefTXT = RefFP.read().decode("utf-8-sig")
	Ref = json.loads(RefTXT, object_pairs_hook = OrderedDict, strict = False)

	InFP = open(INPUT, "rb")
	InTXT = InFP.read().decode("utf-8-sig")
	In = json.loads(InTXT, object_pairs_hook = OrderedDict, strict = False)

	Out = OrderedDict()

	NotFound = 0
	Excessive = 0

	for k, v in Ref.items():
		if k in In and not k in Out:
			Out[k] = In[k]

	for k, v in Ref.items():
		if not k in In:
			if VERBOSE:
				eprint("[NOT FOUND] \"{0}\"".format(k))
			NotFound += 1
			Out[k] = v

	for k, v in In.items():
		if not k in Ref:
			if VERBOSE:
				eprint("[EXCESSIVE] \"{0}\"".format(k))
			Excessive += 1

	OutTXT = json.dumps(Out, ensure_ascii = False, separators=(",\n", ":"))
	OutTXT = OutTXT.replace("{", "{\n", 1)
	OutTXT = "\n}".join(OutTXT.rsplit("}", 1))

	print(OutTXT)

	eprint("--- Statistics ---")
	eprint("Reference: {0}".format(os.path.basename(REFERENCE)))
	eprint("Reference items: {0}".format(len(Ref)))
	eprint("Input: {0}".format(os.path.basename(INPUT)))
	eprint("Input items: {0}".format(len(In)))
	eprint("Output items: {0}".format(len(Out)))
	eprint("Found: {0}".format(len(Out) - NotFound))
	eprint("Not found: {0}".format(NotFound))
	eprint("Excessive: {0}".format(Excessive))
