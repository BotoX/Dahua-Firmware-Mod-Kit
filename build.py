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
import importlib
from configs.config import *

class DahuaBuilder():
	DEPENDENCIES = ["sudo", "mksquashfs", "mkcramfs", "mkimage"]
	def __init__(self, config, debug):
		self.Config = config
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
		self.DahuaFiles = self.Config.DAHUA_FILES

	def CheckDependencies(self):
		Ret = 0
		for dependency in self.DEPENDENCIES:
			if not distutils.spawn.find_executable(dependency):
				self.Logger.error("Missing dependency: '%s'", dependency)
				Ret = 1
		return Ret

	def Build(self, source):
		self.Source = os.path.abspath(source)

		# Check if all required files and directories exist
		self.Logger.info("Checking required files/directories.")
		for Key, Value in self.DahuaFiles.items():
			Passed = True

			if Value["type"] & DAHUA_TYPE.Plain:
				if Value["type"] & DAHUA_TYPE.uImage:
					Path = os.path.join(self.Source, Key + ".raw")
				else:
					Path = os.path.join(self.Source, Key)

				if not os.path.isfile(Path):
					if Value["required"]:
						self.Logger.error("Could not find required file: '%s'", Key)
						raise Exception("Missing requirement!")
					Passed = False

			if Value["type"] & DAHUA_TYPE.uImage:
				if not os.path.isfile(os.path.join(self.Source, Key + ".uImage")):
					if Value["required"]:
						self.Logger.error("Could not find required '.uImage' file for file: '%s'", Key)
						raise Exception("Missing requirement!")
					Passed = False

			if Value["type"] & DAHUA_TYPE.SquashFS:
				if not os.path.isdir(os.path.join(self.Source, Key + ".extracted")):
					if Value["required"]:
						self.Logger.error("Could not find required '.extracted' directory for file: '%s'", Key)
						raise Exception("Missing requirement!")
					Passed = False
				if not os.path.isfile(os.path.join(self.Source, Key + ".raw")):
					if Value["required"]:
						self.Logger.error("Could not find required '.raw' file for file: '%s'", Key)
						raise Exception("Missing requirement!")
					Passed = False

			Value["pass"] = Passed
			if Passed:
				self.Logger.debug("Requirements for '%s' were met.", Key)
			else:
				self.Logger.debug("Requirements for '%s' were NOT met.", Key)

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
		for Key, Value in self.DahuaFiles.items():
			if not Value["pass"]:
				self.Logger.debug("Skipping '%s'.", Key)
				continue

			self.Logger.info("Processing '%s'.", Key)

			if Value["type"] & DAHUA_TYPE.Plain:
				if Value["type"] & DAHUA_TYPE.uImage:
					OrigPath = os.path.join(self.Source, Key + ".raw")
					DestPath = os.path.join(self.BuildDir, Key + ".raw")
					shutil.copyfile(OrigPath, DestPath)
				else:
					OrigPath = os.path.join(self.Source, Key)
					DestPath = os.path.join(self.BuildDir, Key)
					shutil.copyfile(OrigPath, DestPath)
					self.Logger.debug("Adding '%s' to zip file list.", Key)
					self.ZipFileList.append((DestPath, Key))

			if Value["type"] & DAHUA_TYPE.SquashFS:
				if self.Handle_SquashFS(Key) != 0:
					self.Logger.error("'SquashFS' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")

			if Value["type"] & DAHUA_TYPE.CramFS:
				if self.Handle_CramFS(Key) != 0:
					self.Logger.error("'CramFS' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")

			if Value["type"] & DAHUA_TYPE.uImage:
				if self.Handle_uImage(Key) != 0:
					self.Logger.error("'uImage' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")

			if "size" in Value:
				size = Value["size"]
				if Value["type"] & DAHUA_TYPE.uImage:
					size += uImage.HEADER_SIZE

				if os.path.getsize(self.ZipFileList[-1][0]) > size:
					self.Logger.error("Generated file '%s' exceedes maximum allowed filesize!", Key)
					raise Exception("File exceeds maximum allowed filesize!")

		DestPath = os.path.join(self.BuildDir, os.path.basename(self.Source).rstrip(".extracted").rstrip(".bin") + ".bin")
		self.DestFile = open(DestPath, "wb")

		self.Logger.info("Building compressed firmware image.")
		self.ZipFile = zipfile.ZipFile(self.DestFile, mode='w', compression=zipfile.ZIP_DEFLATED)

		for Item in self.ZipFileList:
			self.Logger.debug("Writing '%s' as '%s' to zip file.", Item[0], Item[1])
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

		Result = subprocess.call(["mkimage", "-A", Arch, "-O", OS, "-T", ImageType, "-C", Compression,
								  "-a", LoadAddress, "-e", EntryPoint, "-n", Name, "-d", DataPath, DestPath])

		self.Logger.debug("Adding '%s' to zip file list.", Key)
		self.ZipFileList.append((DestPath, Key))

		return Result

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

		Version = "" if Header["s_major"] == 4 else str(Header["s_major"])
		ConOpts = SquashFS.buildConOpts(Header)

		# Need root to access all files.
		if self.Debug:
			Result = subprocess.call(["sudo", "mksquashfs" + Version, ExtractedDir, DestPath] + ConOpts)
		else:
			Result = subprocess.call(["sudo", "mksquashfs" + Version, ExtractedDir, DestPath] + ConOpts, stdout=subprocess.DEVNULL)

		return Result

	def Handle_CramFS(self, Key):
		ExtractedDir = os.path.join(self.Source, Key + ".extracted")
		OrigPath = os.path.join(self.Source, Key + ".raw")
		DestPath = os.path.join(self.BuildDir, Key + ".raw")

		# Need root to access all files.
		if self.Debug:
			Result = subprocess.call(["sudo", "mkcramfs", ExtractedDir, DestPath])
		else:
			Result = subprocess.call(["sudo", "mkcramfs", ExtractedDir, DestPath], stdout=subprocess.DEVNULL)

		return Result


if __name__ == "__main__":
	logging.basicConfig(format="%(levelname)s\t%(message)s")
	logging.addLevelName(logging.DEBUG, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
	logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
	logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
	logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

	parser = argparse.ArgumentParser(description="Build Dahua firmware images.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Turn on verbose (debugging) output")
	parser.add_argument("-c", "--config", default="auto", help="Configuration to use. (Default: auto)")
	parser.add_argument("source", help="Source Directory (of previously extracted firmware image)")
	args = parser.parse_args()

	Logger = logging.getLogger("main")
	if args.verbose:
		Logger.setLevel(logging.DEBUG)
	else:
		Logger.setLevel(logging.INFO)

	if not os.path.isdir(args.source):
		Logger.error("No such directory: '%s'", args.source)
		sys.exit(1)

	Found = None
	if args.config == "auto":
		Name = os.path.basename(os.path.abspath(args.source))
		for Config in DAHUA_CONFIGS:
			if Config in Name:
				Logger.warn("Autodetected config: %s", Config)
				Found = Config
				break

		if not Found:
			Logger.error("Could not autodetect config!")
	else:
		ArgConfig = args.config.lower()
		for Config in DAHUA_CONFIGS:
			if Config.lower() == ArgConfig:
				Logger.warn("Found config: %s", Config)
				Found = Config
				break

		if not Found:
			Logger.error("Invalid config specified! (Add to configs/config.py DAHUA_CONFIGS if you made a new one)")

	if not Found:
		Logger.info("Please use -c to select the correct config from the following list:")
		for Config in DAHUA_CONFIGS:
			Logger.info("\t" + Config)
		sys.exit(1)

	Config = importlib.import_module("configs." + Found)

	builder = DahuaBuilder(Config, args.verbose)
	if builder.CheckDependencies():
		sys.exit(1)
	builder.Build(args.source)
