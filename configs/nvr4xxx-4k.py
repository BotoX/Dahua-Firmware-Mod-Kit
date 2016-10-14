from .config import *

DAHUA_FILES = OrderedDict([
	("u-boot.bin.img", {
		"required": False,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x00010000
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x0010000
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x0010000
	}),
	("custom-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x0010000
	}),
	("logo-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x0010000
	}),
	("web_mac-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.cramfs,
		"size": 0x0010000
	}),
])
