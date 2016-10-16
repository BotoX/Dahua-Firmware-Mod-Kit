from .config import *

DAHUA_FILES = OrderedDict([
	("Install.lua", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("u-boot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x0080000
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x1700000
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x0380000
	}),
	("custom-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x0080000
	}),
	("logo-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00c0000
	}),
	("web_mac-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x0140000
	}),
])
