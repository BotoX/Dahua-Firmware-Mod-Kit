#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

HEADER_FORMAT = "IIiIIHHHHHHqqqqqqqq"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
HEADER_MAGIC = 0x73717368

ZLIB_COMPRESSION		= 1
LZMA_COMPRESSION		= 2
LZO_COMPRESSION			= 3
XZ_COMPRESSION			= 4
LZ4_COMPRESSION			= 5

ZLIB_FORMAT = "ihh"
ZLIB_SIZE = struct.calcsize(ZLIB_FORMAT)
GZIP_STRATEGIES = ["default", "filtered", "huffman_only", "run_length_encoded", "fixed"]

LZO_FORMAT = "ii"
LZO_SIZE = struct.calcsize(LZO_FORMAT)
LZO_ALGORITHMS = ["lzo1x_1", "lzo1x_1_11", "lzo1x_1_12", "lzo1x_1_15", "lzo1x_999"]

XZ_FORMAT = "ii"
XZ_SIZE = struct.calcsize(XZ_FORMAT)
LZMA_FILTERS = ["x86", "powerpc", "ia64", "arm", "armthumb", "sparc"]

LZ4_FORMAT = "ii"
LZ4_SIZE = struct.calcsize(LZ4_FORMAT)
LZ4_HC = 1

COMPRESSION_STRING = [None, "gzip", "lzma", "lzo", "xz", "lz4"]

# Filesystem flags
SQUASHFS_NOI			= (1 << 0)
SQUASHFS_NOD			= (1 << 1)
SQUASHFS_CHECK			= (1 << 2)
SQUASHFS_NOF			= (1 << 3)
SQUASHFS_NO_FRAG		= (1 << 4)
SQUASHFS_ALWAYS_FRAG	= (1 << 5)
SQUASHFS_DUPLICATE		= (1 << 6)
SQUASHFS_EXPORT			= (1 << 7)
SQUASHFS_NOX			= (1 << 8)
SQUASHFS_NO_XATTR		= (1 << 9)
SQUASHFS_COMP_OPT		= (1 << 10)

# Flag whether block is compressed or uncompressed, bit is set if block is uncompressed
SQUASHFS_COMPRESSED_BIT = (1 << 15)

################################################################################
###
### parseHeader(fh, offset=0) - Parse SquashFS header located at offset in file
###
### Parameters:   fh:      file handle
###               offset:  Optional location of header within file
###
### Returns:      Dictionary of header information
###
def parseHeader(fh, offset=0):
	### Save current position and seek to start position
	startpos = fh.tell()
	fh.seek(offset)

	block = fh.read(HEADER_SIZE)

	### Names of fields in the image header
	keys = ["s_magic", "inodes", "mkfs_time", "block_size", "fragments", "compression", "block_log",
			"flags", "no_ids", "s_major", "s_minor", "root_inode", "bytes_used", "id_table_start",
			"xattr_id_table_start", "inode_table_start", "directory_table_start", "fragment_table_start",
			"lookup_table_start"]

	### Unpack the header into a dictionary of (key,value) pairs
	values = struct.unpack(HEADER_FORMAT, block)
	hd = dict(zip(keys, values))

	### Get compression options if compression is used
	if hd["flags"] & SQUASHFS_COMP_OPT:
		# read size
		block = fh.read(2)
		size = struct.unpack("H", block)[0]
		compressed = not size & SQUASHFS_COMPRESSED_BIT
		if not compressed:
			size &= ~SQUASHFS_COMPRESSED_BIT

		if size and not compressed:
			block = fh.read(size)

			if hd["compression"] & ZLIB_COMPRESSION and size >= ZLIB_SIZE:
				keys = ["compression_level", "window_size", "strategy"]
				values = struct.unpack(ZLIB_FORMAT, block)
				hd["comp_opts"] = dict(zip(keys, values))
				hd["comp_opts"]["strategies"] = []
				for i, strategy in enumerate(GZIP_STRATEGIES):
					if (hd["comp_opts"]["strategy"] >> i) & 1:
						hd["comp_opts"]["strategies"].append(strategy)

			elif hd["compression"] & LZO_COMPRESSION and size >= LZO_SIZE:
				keys = ["algorithm", "compression_level"]
				values = struct.unpack(LZO_FORMAT, block)
				hd["comp_opts"] = dict(zip(keys, values))
				hd["comp_opts"]["algorithm_name"] = LZO_ALGORITHMS[hd["comp_opts"]["algorithm"]]

			elif hd["compression"] & XZ_COMPRESSION and size >= XZ_SIZE:
				keys = ["dictionary_size", "flags"]
				values = struct.unpack(XZ_FORMAT, block)
				hd["comp_opts"] = dict(zip(keys, values))
				hd["comp_opts"]["filters"] = []
				for i, filter in enumerate(LZMA_FILTERS):
					if (hd["comp_opts"]["flags"] >> i) & 1:
						hd["comp_opts"]["filters"].append(filter)

			elif hd["compression"] & LZ4_COMPRESSION and size >= LZ4_SIZE:
				keys = ["version", "flags"]
				values = struct.unpack(LZ4_FORMAT, block)
				hd["comp_opts"] = dict(zip(keys, values))
				hd["comp_opts"]["hc"] = hd["comp_opts"]["flags"] & LZ4_HC

	### Restore saved file position
	fh.seek(startpos)
	return hd

################################################################################
###
### buildConOpts(hd) - Build mksquashfs console options from parsed header
###
### Parameters:   hd:      Dictionary of header information
###
### Returns:      List of console options
###
def buildConOpts(hd):
	args = []
	args.extend(("-comp", COMPRESSION_STRING[hd["compression"]]))
	args.extend(("-b", str(hd["block_size"])))

	if not hd["flags"] & SQUASHFS_EXPORT:
		args.append("-no-exports")
	if hd["flags"] & SQUASHFS_NO_XATTR:
		args.append("-no-xattrs")
	if hd["flags"] & SQUASHFS_NOI:
		args.append("-noI")
	if hd["flags"] & SQUASHFS_NOD:
		args.append("-noD")
	if hd["flags"] & SQUASHFS_NOF:
		args.append("-noF")
	if hd["flags"] & SQUASHFS_NOX:
		args.append("-noX")
	if hd["flags"] & SQUASHFS_NO_FRAG:
		args.append("-no-fragments")
	if hd["flags"] & SQUASHFS_ALWAYS_FRAG:
		args.append("-always-use-fragments")
	if not hd["flags"] & SQUASHFS_DUPLICATE:
		args.append("-no-duplicates")

	if not "comp_opts" in hd:
		return args

	if hd["compression"] & ZLIB_COMPRESSION:
		args.extend(("-Xcompression-level", str(hd["comp_opts"]["compression_level"])))
		args.extend(("-Xwindow-size", str(hd["comp_opts"]["window_size"])))
		args.extend(("-Xstrategy", ','.join(hd["comp_opts"]["strategies"])))

	elif hd["compression"] & LZO_COMPRESSION:
		args.extend(("-Xalgorithm", str(hd["comp_opts"]["algorithm_name"])))
		args.extend(("-Xcompression-level", str(hd["comp_opts"]["compression_level"])))

	elif hd["compression"] & XZ_COMPRESSION:
		args.extend(("-Xbcj", ','.join(hd["comp_opts"]["filters"])))
		args.extend(("-Xdict-size", str(hd["comp_opts"]["dictionary_size"])))

	elif hd["compression"] & LZ4_COMPRESSION:
		if hd["comp_opts"]["hc"]:
			args.extend("-Xhc")

	return args