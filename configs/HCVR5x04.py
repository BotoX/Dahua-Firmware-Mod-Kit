from .config import *

DAHUA_FILES = OrderedDict([
	("Install.lua", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("u-boot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
	}),
	("romfs-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS
	}),
	("web-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS
	}),
	("custom-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS
	}),
	("logo-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS
	}),
	("sign.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
])
