# Dahua-Firmware-Mod-Kit
Unpack and repack Dahua IP camera firmware upgrade images.


### What is this?

A script to extract "[extract.py](extract.py)" a Dahua firmware upgrade image, which may be obtained [here](http://download.dahuatech.com/kit_det.php?cid=4083).

And a script to build "[build.py](build.py)" a working firmware upgrade image from the previously extracted (and possibly modified) firmware upgrade image.


### How do I use this?
First of all, this will only work on Linux. I'm using Archlinux, but any modern distro which meets the following requirements should work.

##### Requirements
- Python 3
- **sudo** - to preserve permissions of the extracted files
- uboot-tools
- squashfs-tools - use [my fork](https://github.com/BotoX/squashfs-tools)!
- cramfs - from [firmware-mod-kit](https://github.com/mirror/firmware-mod-kit/tree/master/src/cramfs-2.x)


### Usage
First extract the right firmware image for you camera:
`./extract.py <firmware.bin>`

A directory "firmware.bin.extracted" will be created.
This directory contains all the files in the firmware.bin (which is just a ZIP file).
Most importantly, the files will also be processed according to "[config.py](config.py)", for example:

- uImage header stripped to &lt;file&gt;.uImage and content to &lt;file&gt;.raw
- SquashFS/CramFS will be extracted to &lt;file&gt;.extracted

This allows the user to study and edit the files in the filesystem.
The script can also compress the extracted files again and will apply the original flags and the correct uImage header.

In order to build a working firmware upgrade image from the extracted files, run:
`./build.py <firmware.bin.extracted>`

This will create a directory "build" where intermediary files will be placed and the new firmware upgrade image will be created: &lt;firmware.bin&gt;

The script will check if all the required files/images are available and if the size of the created images does not exceed the partition size of the camera to **avoid bricking the camera**, other than that **you are on your own**! (You should probably check the sourcecode for mistakes)

This was tested on a DH-IPC-HDW4431C-A cameras and worked fine **for me**, be ready to solder some wires to the serial port if you are poking around with the camera, because the cameras U-Boot does not come with a netconsole and there is no other known recovery procedure (however it does try to TFTP a file "upgrade_info_7db780a713a4.txt").

Also check out the changes I've done on a firmware image [here](https://github.com/BotoX/DH_IPC-HX4XXX-Eos).


### Contributing / Questions / Support
- [This thread](https://www.ipcamtalk.com/showthread.php/13591-Dahua-Firmware-Mod-Kit-Modded-Dahua-Firmware) on ipcamtalk. (Also has example firmware)
- Hit me up on IRC: BotoX @ freenode | rizon
- Issues / PRs welcome.
