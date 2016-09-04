#!/usr/bin/env python3
###############################################################################
###
### Copyright (c) 2012, Rick Richard
### All rights reserved.
###
### Redistribution and use in source and binary forms, with or without
### modification, are permitted provided that the following conditions are met:
###
###    Redistributions of source code must retain the above copyright notice,
###    this list of conditions and the following disclaimer.
###    Redistributions in binary form must reproduce the above copyright
###    notice, this list of conditions and the following disclaimer in the
###    documentation and/or other materials provided with the distribution.
###
###    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
###    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
###    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
###    PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
###    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
###    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
###    TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
###    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
###    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
###    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
###    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

###############################################################################
###
### Python script to pack and unpack U-Boot uImage files
###
###

import os, time, zlib
from struct import pack, unpack, calcsize
from os import fstat
from optparse import OptionParser, OptionGroup

### 64-byte header structure:
### uint32 magic_number
### uint32 header_crc
### uint32 timestamp
### uint32 uImage_size
### uint32 load_address
### uint32 entry_address
### uint32 data_crc
### uint8  os_type
### uint8  architecture
### uint8  image_type
### uint8  compression_type
### uint8  image_name[32]
HEADER_FORMAT = '!7L4B32s'    ### (Big-endian, 7 ULONGS, 4 UCHARs, 32-byte string)
HEADER_SIZE = calcsize(HEADER_FORMAT)    ### Should be 64-bytes
HEADER_MAGIC = 0x27051956

### Image types, from 0 to 14
imageType = [['INVALID', ''],
        ['Standalone', 'standalone'],
        ['Kernel', 'kernel'],
        ['RAMDisk', 'ramdisk'],
        ['Multi-File', 'multi'],
        ['Firmware', 'firmware'],
        ['Script', 'script'],
        ['Filesystem', 'filesystem'],
        ['Flat Device Tree Blob', 'flat_dt'],
        ['Kirkwood Boot', 'kwbimage'],
        ['Freescale IMXBoot', 'imximage'],
        ['Davinci UBL', 'ublimage'],
        ['OMAP Config Header', 'omapimage'],
        ['Davinci AIS', 'aisimage'],
        ['Kernel (any load address)', 'kernel_noload']]

### OS types from 0 to 22
osType = [['INVALID', ''],
        ['OpenBSD', 'openbsd'],
        ['NetBSD', 'netbsd'],
        ['FreeBSD', 'freebsd'],
        ['4.4BSD', '4_4bsd'],
        ['Linux', 'linux'],
        ['SVR4', 'svr4'],
        ['Esix', 'esix'],
        ['Solaris', 'solaris'],
        ['Irix', 'irix'],
        ['SCO', 'sco'],
        ['Dell', 'dell'],
        ['NCR', 'ncr'],
        ['LynxOS', 'lynxos'],
        ['VxWorks', 'vxworks'],
        ['pSOS', 'psos'],
        ['QNX', 'qnx'],
        ['U-Boot Firmware', 'u-boot'],
        ['RTEMS', 'rtems'],
        ['Unity OS', 'unity'],
        ['INTEGRITY', 'integrity'],
        ['OSE', 'ose']]

### CPU Architecture types from 0 to 21
archType = [['INVALID', ''],
        ['Alpha', 'alpha'],
        ['ARM', 'arm'],
        ['Intel x86', 'x86'],
        ['IA64', 'ia64'],
        ['MIPS', 'mips'],
        ['MIPS64', 'mips64'],
        ['PowerPC', 'ppc'],
        ['IBM S390', 's390'],
        ['SuperH', 'sh'],
        ['Sparc', 'sparc'],
        ['Sparc64', 'sparc64'],
        ['M68k', 'm68k'],
        ['MicroBlaze', 'microblaze'],
        ['Nios-II', 'nios2'],
        ['Blackfin', 'blackfin'],
        ['AVR32', 'avr32'],
        ['ST200', 'st200'],
        ['NDS32', 'nds32'],
        ['OpenRISC 1000', 'or1k']]

### Compression types from 0 to 4
compressType = [['uncompressed', 'none'],
        ['gzip compressed', 'gzip'],
        ['bzip2 compressed', 'bzip2'],
        ['lzma compressed', 'lzma'],
        ['lzo compressed', 'lzo']]



################################################################################
###
### fromTable(table, index) - Returns string from lookup table
###
### parameters:   table:   name of table to search
###               index:   index of string to fetch
###
### Returns:      Name fromt table or "unknown" message
###
def fromTable(table, index):
    if index < len(table):
        string = table[index][0]
    else:
        string = "Unknown:" + str(index)
    return string

################################################################################
###
### searchTable(table, value) - Searches a table for value, returns index
###
### parameters:   table:   name of table to search
###               value:   data to search for in table
###
### Returns:      index of value if found, -1 otherwise
###
def searchTable(table, value):
    index = -1
    for i in range(len(table)):
        if table[i][1] == value:
            index = i
            break
    return index

################################################################################
###
### parseHeader(fh, offset=0) - Parse uImage header located at offset in file
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

    try:
        block = fh.read(HEADER_SIZE)
    except IOError:
        print("File read error")
        exit(1)

    ### Names of fields in the image header
    keys = ['magic', 'headerCrc', 'time', 'size', 'loadAddr', 'entryAddr',
            'dataCrc', 'osType', 'arch', 'imageType', 'compression', 'name']

    ### Unpack the header into a dictionary of (key,value) pairs
    values = unpack(HEADER_FORMAT, block)
    hd = dict(zip(keys, values))

    ### if Multi-file image, append file information
    if hd['imageType'] == 4:
        hd['files'] = getMultiFileLengths(fh, fh.tell())
    ### Restore saved file position
    fh.seek(startpos)
    return hd

################################################################################
###
### calculateHeaderCrc(hd) - Calculates the crc for a header
###
### Parameters:   hd:      Dictionary of header
###
### Returns:      crc32 value
###
def calculateHeaderCrc(hd):
    ### Re-pack the list into a binary string
    ### Must calclate header CRC with CRC field set to 0.
    header = pack(HEADER_FORMAT, hd['magic'], 0, hd['time'], hd['size'],
        hd['loadAddr'], hd['entryAddr'], hd['dataCrc'], hd['osType'],
        hd['arch'], hd['imageType'], hd['compression'], hd['name'])
    return (zlib.crc32(header) & 0xffffffff)

################################################################################
###
### crc32File(fh, start, length) - Calculates crc of data segment in a file
###
### Parameters:   fh:      file handle
###               start:   start position (optional)
###               length:  length of segment (optional)
###
def crc32File(fh, start=0, length=float('inf')):
    BLOCKSIZE = 1024*512
    crc32 = 0
    byteCount = 0
    ### Save current position and seek to start position
    startpos = fh.tell()
    fh.seek(start)

    block = fh.read(BLOCKSIZE)
    while block != "":
        byteCount += len(block)
        if byteCount > length:
            extra = byteCount - length
            block = block[:-extra]
            crc32 = zlib.crc32(block, crc32)
            if byteCount >= length:
                break;
        block = fh.read(BLOCKSIZE)

    ### Restore saved file position
    fh.seek(startpos)
    return (crc32 & 0xffffffff)

################################################################################
###
### getMultiFileLengths(fh) - returns list of file lengths in multi-file image
###
### Parameters:   fh:      file handle
###               offset:  location of file lengths
###
def getMultiFileLengths(fh, offset=HEADER_SIZE):
    lengthList = []
    ### Save current position and seek to multi-file table location
    startpos = fh.tell()
    fh.seek(offset)

    block = fh.read(4)
    while block != "":
        length = unpack('!L', block)[0]
        if length == 0:
            break
        lengthList.append(length)
        block = fh.read(4)

    ### Restore saved file position
    fh.seek(startpos)
    return lengthList

################################################################################
###
### dumpHeader(hd) - Dumps header in text form to stdout
###
### Parameters:   hd:      header dictionary
def dumpHeader(hd):
    ### Dump header information and verify CRCs
    if hd['magic'] != HEADER_MAGIC:
        print("Invalid magic number!  This is not a valid uImage file.")
        print("Magic: expected 0x%x, but found %#08x" % (HEADER_MAGIC, hd['magic']))
        return
    print("Image name:\t", end='')
    print(hd['name'].decode("ascii", errors="ignore"))
    print("Created:\t%s" % time.ctime(hd['time']))
    print("Image type:\t", end='')
    print(fromTable(archType, hd['arch']), end=' ')
    print(fromTable(osType, hd['osType']), end=' ')
    print(fromTable(imageType, hd['imageType']), end=' ')
    print("(%s)" % fromTable(compressType, hd['compression']))
    print("Data size:\t%u Bytes" % hd['size'])
    print("Load Address:\t%#08x" % hd['loadAddr'])
    print("Entry Point:\t%#08x" % hd['entryAddr'])


    print("Header CRC:\t%#08x ..." % hd['headerCrc'], end=' ')
    if hd['headerCrc'] == calculateHeaderCrc(hd):
        print("OK")
    else:
        print("Mismatch!  Calculated CRC: %#08x" % str(calculatedHeadedCrc(hd)))

    print("Data CRC:\t%#08x" % hd['dataCrc']) ###,


    ###### Verify Data CRC
    ###print "%#08x" % crc32File(fh)

    if hd['imageType'] == 4:
        print("Contents:")
        for index, length in enumerate(hd['files']):
            print("   Image %u: %u bytes" % (index,length))
    return

################################################################################
###
### dumpToFile(fh, offset, len, filename) - Dumps segment of fh to filename
###
### Parameters:   fh:       Source file handle
###               offset:   Start position in source file
###               length:   Length of segment to copy
###               filename: Name of new file to write contents to
###
def dumpToFile(fh, offset, length, filename):
    ### Save current position and seek to start location
    startpos = fh.tell()
    fh.seek(offset)
    BLOCKSIZE = 1024*512
    df = open(filename, "wb")
    while True:
        if BLOCKSIZE > length:
            BLOCKSIZE = length
        block = fh.read(BLOCKSIZE)
        df.write(block)
        length -= BLOCKSIZE
        if block == "":
            break;

    df.close()
    ### Restore saved file position
    fh.seek(startpos)
    return

################################################################################
###
### imageList(image) - lists contents of image to stdout
###
### Parameters:    image:   filename of image to list
###
def imageList(image):
    try:
        size = os.path.getsize(image)
    except IOError:
        print("inavlid filename:", image)
        exit(1)

    if size < HEADER_SIZE:
        print("File too small!  Not a uImage file.")
        exit(1)

    f = open(image, "rb")
    try:
        data = f.read(HEADER_SIZE)
    except IOError:
        print("File read error")
        f.close()
        exit(1)


    d=parseHeader(f)

    dumpHeader(d)

    ### Dump multi-file headers as well
    if d['imageType'] == 4:
        ### Next image begins after multi-file table
        f.seek(HEADER_SIZE+4+(4*len(d['files'])))
        for index, length in enumerate(d['files']):
            print()
            print("Multi-File Image %u: Header" % (index))
            print("--------------------------")
            mfd = parseHeader(f, f.tell())
            dumpHeader(mfd)
            ### Dump child uImage file
            #dumpToFile(f, f.tell(), length, mfd['name'].rstrip('\0')+".uImage")
            ### Dump payload from child uImage
            #dumpToFile(f, f.tell()+HEADER_SIZE, mfd['size'], mfd['name'].rstrip('\0'))
            f.seek(length,1)
    f.close()


################################################################################
###
### imageExtract(image) - extracts contents of image to file(s)
###
### Parameters:    image:   filename of image to extract
###
def imageExtract(image):

    try:
        size = os.path.getsize(image)
    except IOError:
        print("inavlid filename", image)
        exit(1)

    if size < HEADER_SIZE:
        print("File too small!  Not a uImage file.")
        exit(1)

    f = open(image, "rb")
    try:
        data = f.read(HEADER_SIZE)
    except IOError:
        print("File read error")
        f.close()
        exit(1)


    d=parseHeader(f)

    ### Check for multi-file image
    if d['imageType'] == 4:
        ### Next image begins after multi-file table
        f.seek(HEADER_SIZE+4+(4*len(d['files'])))
        filenames = []
        for index, length in enumerate(d['files']):
            mfd = parseHeader(f, f.tell())
            filename = mfd['name'].rstrip('\0')
            if filename == "":
                filename = "image"+index
            ### Prevent overwriting files with the same name
            if filename in filenames:
                suffix = 1
                while filename+"_"+str(suffix) in filenames:
                    suffix += 1
                filename = filename + "_" + str(suffix)
            filenames.append(filename)
            ### Dump child uImage file
            print(filename+".uImage")
            dumpToFile(f, f.tell(), length, filename+".uImage")
            ### Dump payload from child uImage
            print(filename)
            dumpToFile(f, f.tell()+HEADER_SIZE, mfd['size'], filename)
            f.seek(length,1)
    else:
        filename = d['name'].rstrip('\0')
        if filename == "":
            filename = "image0"
        print(d['name'].rstrip('\0'))
        dumpToFile(f, HEADER_SIZE, d['size'], filename)
    f.close()

################################################################################
###
### imageCreate(options, image) - creates uImage with provided options
###
### Parameters:    image:   filename of image to create
###                options: uImage header options from command-line
###
def imageCreate(options, image):
    ifh = open(image, 'w+b')
    os = searchTable(osType, options.osType)
    arch = searchTable(archType, options.architecture)
    it = searchTable(imageType, options.imageType)
    le = int(options.loadaddr, 0)
    ep = int(options.entryaddr, 0)
    comp = searchTable(compressType, options.compression)
    dcrc = 0
    hcrc = 0
    size = 0
    data = str()
    ### unix timestamp (or set to 0 to be like Palm)
    ctime = int(time.time())

    ### Check if multi-image
    if it == 4:
        lenTable = []
        for filename in options.filespec.split(":"):
            dfh = open(filename, 'rb')
            lenTable.append(fstat(dfh.fileno()).st_size)
            data += dfh.read()
            dfh.close()
        lenTable.append(0)
        fmt = "!" + str(len(lenTable)) + "L"
        data = pack(fmt, *lenTable) + data
    else:
        dfh = open(options.filespec, 'rb')
        data = dfh.read()
        dfh.close()
    size = len(data)
    dcrc = zlib.crc32(data) & 0xFFFFFFFF
    header = pack(HEADER_FORMAT, HEADER_MAGIC, 0, ctime, size,
        le, ep, dcrc, os, arch, it, comp, options.imagename)
    hcrc = zlib.crc32(header) & 0xFFFFFFFF
    header = pack(HEADER_FORMAT, HEADER_MAGIC, hcrc, ctime, size,
        le, ep, dcrc, os, arch, it, comp, options.imagename)
    ifh.write(header)
    ifh.write(data)
    ifh.close()
    imageList(image)

################################################################################
###
### Main program body
###
def main():
    usage = "\n\t%prog -l image" \
            "\n\t%prog -c [options] image" \
            "\n\t%prog -x image" \
            "\n\t%prog -h"
    parser = OptionParser(usage)
    parser.add_option("-l", action = "store_true", dest = "imageList",
            help = "list image contents")
    parser.add_option("-c", action = "store_true", dest = "imageCreate",
            help = "create new image")
    parser.add_option("-x", action = "store_true", dest = "imageExtract",
            help="extract image contents")

    group = OptionGroup(parser, "Creation Options", "-c -A arch -O os -T" \
            " type -C comp -a addr -e ep -n name -d data_file[:data_file...] image")
    group.add_option("-A", dest = "architecture", help = "set architecture to 'arch'")
    group.add_option("-O", dest = "osType", help = "set operating system to 'os'")
    group.add_option("-T", dest = "imageType", help = "set image type to 'type'")
    group.add_option("-C", dest = "compression", help = "set compression to 'comp'")
    group.add_option("-a", dest = "loadaddr", help = "iset load address to 'addr'")
    group.add_option("-e", dest = "entryaddr", help = "iset entry point to 'ep'")
    group.add_option("-n", dest = "imagename", help = "set image name to 'name'")
    group.add_option("-d", dest = "filespec", help = "image data from 'datafile'")
    parser.set_defaults(osType="linux", loadaddr="0", entryaddr="0", imagename="",
            compression="none", architecture="x86")
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    image = args[0]

    if options.imageList:
        if options.imageCreate or options.imageExtract:
            parser.error("-l, -c, and -x are mutually exclusive")
        imageList(image)
    elif options.imageExtract:
        if options.imageList or options.imageCreate:
            parser.error("-l, -c, and -x are mutually exclusive")
        imageExtract(image)
    elif options.imageCreate:
        if options.imageList or options.imageExtract:
            parser.error("-l, -c, and -x are mutually exclusive")
        if not options.imageType:
            parser.error("Must specify image type")
        if not options.filespec:
            parser.error("Must specify data file")
        imageCreate(options, image)

    return

if __name__ == "__main__":
   main()
