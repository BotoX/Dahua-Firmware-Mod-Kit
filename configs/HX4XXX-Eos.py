from .config import *

DAHUA_FILES = OrderedDict([
	("hwid", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("Install", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("kernel.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00180000
	}),
	("dhboot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00030000
	}),
	("romfs-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x000e0000
	}),
	("user-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x008c0000
	}),
	("web-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00280000
	}),
	("pd-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00020000
	}),
	("custom-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00020000
	}),
	("partition-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00020000
	}),
	("check.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.Plain
	})
])
