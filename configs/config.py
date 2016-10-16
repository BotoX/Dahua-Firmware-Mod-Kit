from enum import IntEnum
from collections import OrderedDict

class DAHUA_TYPE(IntEnum):
	Plain = 1
	uImage = 2
	SquashFS = 4
	CramFS = 8

DAHUA_CONFIGS = [
	"HX4XXX-Eos", "HX4X2X-Themis",
	"VTO2000A",
	"NVR4XXX-4K", "NVR4xxx"
]
