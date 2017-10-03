from .config import *

DAHUA_FILES = OrderedDict([
	("Install", {
		"required": True,
		"type": DAHUA_TYPE.Plain
	}),
	("kernel.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00580000
	}),
	("dhboot-min.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00100000
	}),
	("dhboot.bin.img", {
		"required": True,
		"type": DAHUA_TYPE.Plain,
		"size": 0x00100000
	}),
	("romfs-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00400000
	}),
	("user-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x01c80000
	}),
	("web-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00800000
	}),
	("pd-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00340000
	}),
	("custom-x.squashfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.SquashFS,
		"size": 0x00340000
	}),
	("partition-x.cramfs.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.CramFS,
		"size": 0x00100000
	}),
	("check.img", {
		"required": True,
		"type": DAHUA_TYPE.uImage | DAHUA_TYPE.Plain
	})
])
