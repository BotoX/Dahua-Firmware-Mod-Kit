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
import importlib
from configs.config import *

class DahuaExtractor():
	DEPENDENCIES = ["sudo", "unsquashfs", "cramfsck"]
	def __init__(self, config, debug):
		self.Config = config
		self.Debug = debug
		self.Logger = logging.getLogger(__class__.__name__)
		if self.Debug:
			self.Logger.setLevel(logging.DEBUG)
		else:
			self.Logger.setLevel(logging.INFO)
		self.Source = None
		self.SourceFile = None
		self.ZipFile = None
		self.DahuaFiles = self.Config.DAHUA_FILES

	def CheckDependencies(self):
		Ret = 0
		for dependency in self.DEPENDENCIES:
			if not distutils.spawn.find_executable(dependency):
				self.Logger.error("Missing dependency: '%s'", dependency)
				Ret = 1
		return Ret

	def Extract(self, source):
		self.Source = os.path.abspath(source)
		self.Logger.debug("Opening source file '%s'", self.Source)
		self.SourceFile = open(self.Source, "r+b")

		Header = self.SourceFile.read(2)
		self.SourceFile.seek(0)
		self.Logger.debug("Checking source header: '%s'", Header.decode("ascii", errors="ignore"))
		if Header == b'DH':
			self.Logger.debug("Patching source header to: 'PK'")
			self.SourceFile.write(b"PK")
			self.SourceFile.seek(0)
		elif Header == b'PK':
			self.Logger.debug("Source header is already 'PK' ? (Should be 'DH')")
		else:
			self.Logger.error("Unknown source header! Is this really a dahua firmware upgrade image?")
			raise Exception("Unknown source header!")

		self.Logger.debug("Opening source as zipfile.")
		self.ZipFile = zipfile.ZipFile(self.SourceFile)

		self.Logger.debug("Checking zipfile CRC.")
		ZipTestResult = self.ZipFile.testzip()
		if ZipTestResult:
			self.Logger.error("ZipFile corrupt, first file which did not pass test: '%s'", ZipTestResult)
			raise Exception("ZipFile corrupt!")

		self.Logger.debug("Zipfile contents:")
		for index, item in enumerate(self.ZipFile.filelist):
			self.Logger.debug("%s: %s (%d bytes)", index, item.filename, item.file_size)

		self.DestDir = os.path.basename(self.Source) + ".extracted"
		if os.path.exists(self.DestDir):
			self.Logger.error("Destination directory '%s' already exists! Please delete it if you want to continue.", os.path.basename(self.DestDir))
			raise Exception("Destination directory already exists!")

		self.Logger.info("Extracting %d files to: '%s'", len(self.ZipFile.filelist), self.DestDir)
		self.ZipFile.extractall(path=self.DestDir)
		self.ExtractedFiles = self.ZipFile.namelist()

		self.Logger.debug("Closing zipfile.")
		self.ZipFile.close()
		self.ZipFile = None

		# Call Handle() for every extracted file
		for Key in self.ExtractedFiles:
			if Key not in self.DahuaFiles:
				self.Logger.warning("Unrecognized file: '%s'.", Key)
				continue

			Value = self.DahuaFiles[Key]
			self.Logger.info("Processing '%s'.", Key)

			if Value["type"] & DAHUA_TYPE.uImage:
				if self.Handle_uImage(Key) != 0:
					self.Logger.error("'uImage' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")
				# for the next handler
				Key += ".raw"

			if Value["type"] & DAHUA_TYPE.Plain:
				pass

			if Value["type"] & DAHUA_TYPE.SquashFS:
				if self.Handle_SquashFS(Key) != 0:
					self.Logger.error("'SquashFS' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")

			if Value["type"] & DAHUA_TYPE.CramFS:
				if self.Handle_CramFS(Key) != 0:
					self.Logger.error("'CramFS' handler returned non-zero return value for file: '%s'", Key)
					raise Exception("Handler returned non-zero return value!")

		self.Logger.debug("Reverting source header patch.")
		self.SourceFile.seek(0)
		self.SourceFile.write(b"DH")

		self.Logger.debug("Closing source file.")
		self.SourceFile.close()
		self.SourceFile = None
		self.Source = None

	def Handle_uImage(self, Key):
		Path = os.path.join(self.DestDir, Key)
		OrigFile = open(Path, "rb")
		# Read uImage header.
		Header = uImage.parseHeader(OrigFile)
		if Header["magic"] != uImage.HEADER_MAGIC:
			OrigFile.close()
			self.Logger.error("Invalid uImage magic number!")
			return 1

		# Save uImage header
		HeaderFile = open(Path + ".uImage", "wb")
		HeaderFile.write(OrigFile.read(uImage.HEADER_SIZE))
		HeaderFile.close()

		# Save raw image
		RawFile = open(Path + ".raw", "wb")
		shutil.copyfileobj(OrigFile, RawFile)
		RawFile.close()

		OrigFile.close()
		return 0

	def Handle_SquashFS(self, Key):
		Path = os.path.join(self.DestDir, Key)
		DestDir = Path.rstrip(".raw") + ".extracted"
		# Need root to preserve permissions.
		if self.Debug:
			Result = subprocess.call(["sudo", "unsquashfs", "-d", DestDir, Path])
		else:
			Result = subprocess.call(["sudo", "unsquashfs", "-d", DestDir, Path], stdout=subprocess.DEVNULL)

		return Result

	def Handle_CramFS(self, Key):
		Path = os.path.join(self.DestDir, Key)
		DestDir = Path.rstrip(".raw") + ".extracted"
		# Need root to preserve permissions.
		if self.Debug:
			Result = subprocess.call(["sudo", "cramfsck", "-x", DestDir, Path])
		else:
			Result = subprocess.call(["sudo", "cramfsck", "-x", DestDir, Path], stdout=subprocess.DEVNULL)

		return Result

if __name__ == "__main__":
	logging.basicConfig(format="%(levelname)s\t%(message)s")
	logging.addLevelName(logging.DEBUG, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
	logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
	logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
	logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

	parser = argparse.ArgumentParser(description="Extract Dahua firmware images.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Turn on verbose (debugging) output")
	parser.add_argument("-c", "--config", default="auto", help="Configuration to use. (Default: auto)")
	parser.add_argument("source", help="Source File")
	args = parser.parse_args()

	Logger = logging.getLogger("main")
	if args.verbose:
		Logger.setLevel(logging.DEBUG)
	else:
		Logger.setLevel(logging.INFO)

	if not os.path.isfile(args.source):
		Logger.error("No such file: '%s'", args.source)
		sys.exit(1)

	Found = None
	if args.config == "auto":
		Name = os.path.basename(os.path.abspath(args.source)).lower()
		for Config in DAHUA_CONFIGS:
			if Config.lower() in Name:
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

	extractor = DahuaExtractor(Config, args.verbose)
	if extractor.CheckDependencies():
		sys.exit(1)
	extractor.Extract(args.source)
