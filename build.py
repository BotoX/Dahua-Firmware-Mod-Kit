#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import distutils.spawn
import logging
import zipfile
import subprocess
import shutil
import uImage
import SquashFS
from config import *

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

class DahuaBuilder():
	DEPENDENCIES = ["sudo", "mksquashfs", "mkimage"]
	def __init__(self, debug):
		self.Debug = debug
		self.Logger = logging.getLogger(__class__.__name__)
		if self.Debug:
			self.Logger.setLevel(logging.DEBUG)
		else:
			self.Logger.setLevel(logging.INFO)
		self.Source = None
		self.BuildDir = None
		self.ZipFileList = None
		self.DestFile = None
		self.ZipFile = None

	def CheckDependencies(self):
		Ret = 0
		for dependency in self.DEPENDENCIES:
			if not distutils.spawn.find_executable(dependency):
				self.Logger.error("Missing dependency: '{}'".format(dependency))
				Ret = 1
		return Ret

	def Build(self, source):
		self.Source = os.path.abspath(source)

		# Check if all required files and directories exist
		self.Logger.info("Checking required files/directories.")
		for Key, Value in DAHUA_FILES.items():
			Passed = True

			if Value["type"] & DAHUA_TYPE.Plain:
				if Value["type"] & DAHUA_TYPE.uImage:
					Path = os.path.join(self.Source, Key + ".raw")
				else:
					Path = os.path.join(self.Source, Key)

				if not os.path.isfile(Path):
					if Value["required"]:
						self.Logger.error("Could not find required file: '{}'".format(Key))
						raise Exception("Missing requirement!")
					Passed = False

			if Value["type"] & DAHUA_TYPE.uImage:
				if not os.path.isfile(os.path.join(self.Source, Key + ".uImage")):
					if Value["required"]:
						self.Logger.error("Could not find required '.uImage' file for file: '{}'".format(Key))
						raise Exception("Missing requirement!")
					Passed = False

			if Value["type"] & DAHUA_TYPE.SquashFS:
				if not os.path.isdir(os.path.join(self.Source, Key + ".extracted")):
					if Value["required"]:
						self.Logger.error("Could not find required '.extracted' directory for file: '{}'".format(Key))
						raise Exception("Missing requirement!")
					Passed = False
				if not os.path.isfile(os.path.join(self.Source, Key + ".raw")):
					if Value["required"]:
						self.Logger.error("Could not find required '.raw' file for file: '{}'".format(Key))
						raise Exception("Missing requirement!")
					Passed = False

			Value["pass"] = Passed
			if Passed:
				self.Logger.debug("Requirements for '{}' were met.".format(Key))
			else:
				self.Logger.debug("Requirements for '{}' were NOT met.".format(Key))

		# Check if build directory exists in source dir
		self.BuildDir = os.path.join(self.Source, "build")

		if os.path.isdir(self.BuildDir):
			self.Logger.info("Build directory already exists, deleting.")
			shutil.rmtree(self.BuildDir)

		# Create build dir
		self.Logger.info("Creating 'build' directory.")
		os.mkdir(self.BuildDir)

		self.ZipFileList = []

		#
		self.Logger.info("Starting build process.")
		for Key, Value in DAHUA_FILES.items():
			if not Value["pass"]:
				self.Logger.debug("Skipping '{}'.".format(Key))
				continue

			self.Logger.info("Processing '{}'.".format(Key))

			if Value["type"] & DAHUA_TYPE.Plain:
				if Value["type"] & DAHUA_TYPE.uImage:
					OrigPath = os.path.join(self.Source, Key + ".raw")
					DestPath = os.path.join(self.BuildDir, Key + ".raw")
					shutil.copyfile(OrigPath, DestPath)
				else:
					OrigPath = os.path.join(self.Source, Key)
					DestPath = os.path.join(self.BuildDir, Key)
					shutil.copyfile(OrigPath, DestPath)
					self.Logger.debug("Adding '{}' to zip file list.".format(Key))
					self.ZipFileList.append((DestPath, Key))

			if Value["type"] & DAHUA_TYPE.SquashFS:
				if self.Handle_SquashFS(Key) != 0:
					self.Logger.error("'SquashFS' handler returned non-zero return value for file: '{}'".format(Key))
					raise Exception("Handler returned non-zero return value!")

			if Value["type"] & DAHUA_TYPE.CramFS:
				if self.Handle_CramFS(Key) != 0:
					self.Logger.error("'CramFS' handler returned non-zero return value for file: '{}'".format(Key))
					raise Exception("Handler returned non-zero return value!")

			if Value["type"] & DAHUA_TYPE.uImage:
				if self.Handle_uImage(Key) != 0:
					self.Logger.error("'uImage' handler returned non-zero return value for file: '{}'".format(Key))
					raise Exception("Handler returned non-zero return value!")

			if "size" in Value:
				size = Value["size"]
				if Value["type"] & DAHUA_TYPE.uImage:
					size += uImage.HEADER_SIZE

				if os.path.getsize(self.ZipFileList[-1][0]) > size:
					self.Logger.error("Generated file '{}' exceedes maximum allowed filesize!".format(Key))
					raise Exception("File exceeds maximum allowed filesize!")

		DestPath = os.path.join(self.BuildDir, os.path.basename(self.Source).rstrip(".extracted").rstrip(".bin") + ".bin")
		self.DestFile = open(DestPath, "wb")

		self.Logger.info("Building compressed firmware image.")
		self.ZipFile = zipfile.ZipFile(self.DestFile, mode='x', compression=zipfile.ZIP_DEFLATED)

		for Item in self.ZipFileList:
			self.Logger.debug("Writing '{0}' as '{1}' to zip file.".format(Item[0], Item[1]))
			self.ZipFile.write(Item[0], Item[1])

		self.ZipFile.close()
		self.ZipFile = None

		# Write DH header
		self.Logger.debug("Patching zip header from 'PK' to 'DH'.")
		self.DestFile.seek(0)
		self.DestFile.write(b"DH")

		self.DestFile.close()
		self.DestFile = None

	def Handle_uImage(self, Key):
		OrigPath = os.path.join(self.Source, Key + ".uImage")
		DestPath = os.path.join(self.BuildDir, Key)
		DataPath = os.path.join(self.BuildDir, Key + ".raw")

		# Read uImage header of the original file.
		OrigFile = open(OrigPath, "rb")
		Header = uImage.parseHeader(OrigFile)
		OrigFile.close()

		if Header["magic"] != uImage.HEADER_MAGIC:
			OrigFile.close()
			self.Logger.error("Invalid uImage magic number!")
			return 1

		Arch = uImage.archType[Header["arch"]][1]
		OS = uImage.osType[Header["osType"]][1]
		ImageType = uImage.imageType[Header["imageType"]][1]
		Compression = uImage.compressType[Header["compression"]][1]
		LoadAddress = str(hex(Header["loadAddr"]))[2:]
		EntryPoint = str(hex(Header["entryAddr"]))[2:]
		Name = Header["name"].decode("ascii", errors="ignore").rstrip('\0')

		Result = subprocess.run(["mkimage", "-A", Arch, "-O", OS, "-T", ImageType, "-C", Compression,
								 "-a", LoadAddress, "-e", EntryPoint, "-n", Name, "-d", DataPath, DestPath])

		self.Logger.debug("Adding '{}' to zip file list.".format(Key))
		self.ZipFileList.append((DestPath, Key))

		return Result.returncode

	def Handle_SquashFS(self, Key):
		ExtractedDir = os.path.join(self.Source, Key + ".extracted")
		OrigPath = os.path.join(self.Source, Key + ".raw")
		DestPath = os.path.join(self.BuildDir, Key + ".raw")

		# Read SquashFS header to figure out compression and blocksize of the original file.
		OrigFile = open(OrigPath, "rb")
		Header = SquashFS.parseHeader(OrigFile)
		OrigFile.close()

		if Header["s_magic"] != SquashFS.HEADER_MAGIC:
			OrigFile.close()
			self.Logger.error("Invalid SquashFS magic number!")
			return 1

		ConOpts = SquashFS.buildConOpts(Header)

		# Need root to access all files.
		if self.Debug:
			Result = subprocess.run(["sudo", "mksquashfs", ExtractedDir, DestPath, *ConOpts])
		else:
			Result = subprocess.run(["sudo", "mksquashfs", ExtractedDir, DestPath, *ConOpts], stdout=subprocess.DEVNULL)

		return Result.returncode

	def Handle_CramFS(self, Key):
		# idk how to extract this or pack in this case
		OrigPath = os.path.join(self.Source, Key + ".raw")
		DestPath = os.path.join(self.BuildDir, Key + ".raw")
		shutil.copyfile(OrigPath, DestPath)
		return 0


if __name__ == "__main__":
	logging.basicConfig(format="%(levelname)s\t%(message)s")
	logging.addLevelName(logging.DEBUG, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
	logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
	logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
	logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

	parser = argparse.ArgumentParser(description="Build Dahua firmware images.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Turn on verbose (debugging) output")
	parser.add_argument("source", help="Source Directory (of previously extracted firmware image)")
	args = parser.parse_args()

	if not os.path.isdir(args.source):
		eprint("No such directory: '{}'".format(args.source))
		sys.exit(1)

	builder = DahuaBuilder(args.verbose)
	if builder.CheckDependencies():
		sys.exit(1)
	builder.Build(args.source)
