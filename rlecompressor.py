#!/usr/bin/env python3

import sys
import os

# some people out there are still using old versions of python that does not have the following module, so we check for that
try:
    import shutil
except ImportError:
    sys.exit('error: python 3.3 or above is required for this to operate')

"""
RLE (run-length encoding) compression tool

Data is compressed by counting the occurrences of one byte before a different byte.
The occurrence count of that one byte is then associated with that byte and it goes on.
For instance, if there were three 0x08 bytes together, when compressed, this is represented as '0x08 0x02' (starts from 0x00).
Further bytes are appended. Index 0 would return the first byte and index 1 returns the occurrence count.
Index 2 would be the second byte, index 3 is the occurrence count for that byte. And so forth.

To decompress the compressed data, the occurrence count is used to determine how much of each byte needs to be put out.
"""

# read operation
def unpack(file):
    try:
        f = open(file, 'rb')
    except FileNotFoundError:
        sys.exit('error: failed to read input file as it does not exist') # file does not exist
    except IOError:
        sys.exit('error: failed to read input file. are permissions correctly set?') # generic i/o error -- likely permissions
    fileContent = f.read()
    f.close()
    return fileContent

# free space check
def storage(file, dat):
    path = os.path.dirname(os.path.abspath(file)) # get full destination file path but omit file name to keep shutil happy
    free = shutil.disk_usage(path).free
    remainingSpace = free - len(dat)
    # verify if user has enough free storage to write the data
    if remainingSpace <= 0:
        sys.exit('error: output file destination has insufficient space')
    return

# write operation
def pack(file, dat):
    try:
        combineDat = bytes(dat) # change list to bytes data type before write
    except ValueError:
        sys.exit('error: simultaneous byte count exceeded 256') # working with base 16 and a single byte for counting, so we cannot work with fairly large numbers
    try:
        f = open(file, 'wb')
    except FileNotFoundError:
        sys.exit('error: failed to write output file. ensure the destination directory exists.') # specified directory does not exist
    except IOError:
        sys.exit('error: failed to write output file. are permissions correctly set?') # generic i/o error -- likely permissions
    storage(file, combineDat) # storage check
    f.write(combineDat)
    f.flush()
    os.fsync(f)
    f.close()
    return combineDat

# compresses content from input file using run-length encoding lossless compression
def compress(input, output):
    compressionBuffer = [] # init buffer
    trackedByte = None # init currently used byte

    unpackedDat = unpack(input)

    for byte in unpackedDat:
        if byte != trackedByte:
            # create a new byte
            trackedCount = 0x00 # (re)set counter
            trackedByte = byte # set new byte
            compressionBuffer.append(byte) # create new byte entry
            compressionBuffer.append(trackedCount) # create new byte counter
            
        elif trackedByte != None:
            # update current counter
            trackedCount = trackedCount + 0x01 # increment counter

            compressionBuffer[-1] = trackedCount # update last byte counter in buffer
            
    pack(output, compressionBuffer)

    return compressionBuffer

# decompresses content from input file containing run-length encoding lossless compressed data
def decompress(input, output):
    decompressionBuffer = [] # init buffer

    byteBegin = 0
    byteEnd = 1

    dat = unpack(input)

    # integrity check (ensure it is not empty but is divisible by two)
    if len(dat) == 0 or len(dat) % 2 == 1:
        sys.exit('error: bad data')

    for _ in range(len(dat) - 4):
        # take first byte for sort of byte and then next for amount (taking the first one into account)
        for _ in range(dat[byteEnd] + 1):
            decompressionBuffer.append(dat[byteBegin])

        # check if no more bytes
        try:
            dat[byteEnd + 1]
        except IndexError:
            break

        byteBegin = byteBegin + 2
        byteEnd = byteEnd + 2

    pack(output, decompressionBuffer)

    return decompressionBuffer


# argument handling
try:
    modeType = sys.argv[1]
    fileInput = sys.argv[2]
    fileOutput = sys.argv[3]
except IndexError:
    fileName = sys.argv[0]
    sys.exit('syntax: ' + fileName + ' [c (compress) | d (decompress)] [input file] [output file]')

# modes
if modeType == 'c':
    compress(fileInput, fileOutput)
elif modeType == 'd':
    decompress(fileInput, fileOutput)
else:
    sys.exit('error: no such mode')
