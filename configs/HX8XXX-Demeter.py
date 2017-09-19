from .config import *

DAHUA_FILES = OrderedDict([
	("check.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.Plain
	}),
	("Install", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("kernel.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00500000
	}),
	("dhboot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00100000
	}),
	("romfs-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00800000
	}),
	("user-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x01980000
	}),
	("web-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00800000
	}),
	("pd-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00020000
	}),
	("custom-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00380000
	}),
	("partition-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00100000
	})
])
