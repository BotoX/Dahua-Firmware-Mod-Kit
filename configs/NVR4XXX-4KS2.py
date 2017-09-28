from .config import *

DAHUA_FILES = OrderedDict([
	("Install.lua", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("u-boot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00300000
	}),
	("uImage.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00a00000
	}),
	("romfs-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x03600000
	}),
	("web-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00a00000
	}),
	("custom-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00200000
	}),
	("logo-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00300000
	})
])
