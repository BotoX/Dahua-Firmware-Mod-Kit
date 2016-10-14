from enum import IntEnum
from collections import OrderedDict

class DAHUA_TYPE(IntEnum):
	Plain = 1
	uImage = 2
	SquashFS = 4
	CramFS = 8

DAHUA_FILES = OrderedDict([
	("Install", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("dm365_ubl_boot_16M.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00030000
	}),
	("kernel-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x000e0000
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x000e0000
	}),
	("user-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x008c0000
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00280000
	}),
	("data-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x008c0000
	}),
	("pd-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00020000
	}),
	("custom-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00020000
	}),

])
