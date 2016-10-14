from .config import *

DAHUA_FILES = OrderedDict([
	("Install", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("dm365_ubl_boot_16M.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00040000
	}),
	("kernel-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00200000
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00300000
	}),
	("user-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00600000
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00200000
	}),
	("data-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00120000
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
