from enum import IntEnum
from collections import OrderedDict

class DAHUA_TYPE(IntEnum):
	Plain = 1
	uImage = 2
	SquashFS = 4
	CramFS = 8

DAHUA_CONFIGS = ["Eos", "Themis", "VTO"]
