# Import the tqdm progress bar library
from tqdm import trange

# EEPROM Configuration constants
bytesPerPage = 64
totalPages = 512
totalBytes = bytesPerPage * totalPages

# Output Configuration Constants
outputChar = 0x00
outputFileName = "Blank_Dump.hex"

# Initialise a progress bar for the read operation and the output file
with open(outputFileName, "wb") as dumpFile:
    for byteAddress in trange(0, totalBytes, unit = " bytes"):
        dumpFile.write(outputChar.to_bytes(1))


