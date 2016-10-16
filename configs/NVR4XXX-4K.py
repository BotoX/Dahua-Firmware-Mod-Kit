from .config import *

DAHUA_FILES = OrderedDict([
	("Install.lua", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("u-boot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00080000
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x01700000
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00380000
	}),
	("custom-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00080000
	}),
	("logo-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x000c0000
	}),
	("web_mac-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00280000
	})
])
