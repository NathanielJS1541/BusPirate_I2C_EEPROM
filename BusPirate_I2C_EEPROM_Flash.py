# Import argparse to handle command line arguments and help texts
import argparse

# Import Path from Pathlib to handle directories
from pathlib import Path

# Import the pyBusPirateLite library
from pyBusPirateLite.I2C import I2C

# Import the tqdm progress bar library
from tqdm import tqdm

# EEPROM Constants
MAXIMUM_MEMORY_ADDRESS = 0xFFFF  # These scripts only support 16-bit memory addresses.
MAXIMUM_I2C_ADDRESS = 0b01111111 # 7 bits is the largest possible I2C address, as the least significant bit denotes read (1) or write (0) mode.

# Colours for output to terminal (Blender Style)
class OutputColours:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    VERBOSE = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Function to allow the argparser to convert a hex string to an int
def auto_int(x):
    return int(x, 0)

# ------------------------------------------------------------------------------------------------ Argument Parser -------------------------------------------------------------------------------------------------
# Set up the argument parser to retreive inputs from the user
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-a", "--address",        dest="address",       help="The I2C address of the EEPROM module (Note: not the read or write addresses).",    type=auto_int,  required=False, default=hex(0x50))
parser.add_argument("-c", "--clock-speed",    dest="clockSpeed",    help="The clock speed to use when communicating with the EEPROM module.",                type=str,  required=False, default="400kHz", choices=["400kHz", "100kHz", "50kHz", "5kHz"])
parser.add_argument("-b", "--bytes-per-page", dest="bytesPerPage",  help="The number of bytes per page listed in the EEPROM datasheet.",                     type=int,  required=True)
parser.add_argument("-p", "--total-pages",    dest="totalPages",    help="The number of memory pages listed in the EEPROM datasheet.",                       type=int,  required=True)
parser.add_argument("-i", "--input-file",     dest="inputFile",     help="Path to the dump file that will be used to flash to the EEPROM.",                  type=Path, required=True)
parser.add_argument("-e", "--enable-pullups", dest="enablePullups", help="Enable the internal pullup resistors in the BusPirate. Disabled by default.",      action="store_true")
parser.add_argument("-v", "--verbose",        dest="verbose",       help="Print verbose messages.",                                                          action="store_true")

# Parse the user inputs using the argument parser
args = parser.parse_args()
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------ Input Valudation ------------------------------------------------------------------------------------------------
# Check that a valid I2C address has been provided
if args.address > MAXIMUM_I2C_ADDRESS:
    raise ValueError(f"{OutputColours.ERROR}[ERR] The maximum I2C address should be {hex(MAXIMUM_I2C_ADDRESS)}, but {hex(args.address)} was provided.{OutputColours.END}")

# Convert the I2C address to a read and write address. The I2C address is the 7 most significant bits of the address, as the least significant bit denotes read (1) or write (0) mode.
READ_ADDRESS = (args.address << 1) | 0b00000001   # The EEPROM read address is the I2C address but bit shifted and with a 1 in the LSB
WRITE_ADDRESS = (args.address << 1) & 0b11111110  # The EEPROM write address is the I2C address but bit shifted and with a 0 in the LSB

# Calculate the total number of bytes to generate
totalBytes = args.bytesPerPage * args.totalPages

# Ensure that the specified file can be writted to a device with 16-bit addresses, as this is what the other scripts here support.
if totalBytes > MAXIMUM_MEMORY_ADDRESS:
    raise ValueError(f"{OutputColours.ERROR}[ERR] These scripts can operate with up to 16-bit memory addresses. The maximum possible address is {MAXIMUM_MEMORY_ADDRESS}, but up to address {totalBytes} was "
                     f"requested. Consider lowering the pages (-p) value.{OutputColours.END}")

# Ensure the input file exists and is a valid file
if not args.inputFile.exists():
    # If the file does not exist, report the error to the user
    raise SystemExit(f"{OutputColours.ERROR}[ERR] The specified input file does not exist.{OutputColours.END}")
elif args.inputFile.exists() and not args.inputFile.is_file():
    # In this case, it appears as if the input specified is not a file, report the error to the user
    raise SystemExit(f"{OutputColours.ERROR}[ERR] The specified input does not appear to be a valid file.{OutputColours.END}")

# Get the size of the input file in bytes
fileSize = args.inputFile.stat().st_size

# Check that the file will fit on the EEPROM
if fileSize > totalBytes:
    raise IndexError("Input file size is larger than the specified EEPROM size.")
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Create a busPirate object configured to communicate over I2C
busPirate = I2C()

# Set the I2C clock speed of the BusPirate
busPirate.speed = args.clockSpeed

# Configure the BusPirate's power output and internal pullup resistors
busPirate.configure(power = True, pullup = args.enablePullups)

# Send a start bit
busPirate.start()

# Initialise the input file and a progress bar for the write operation
with open(args.inputFile, "rb") as dumpFile:
    with tqdm(total = fileSize, unit = " bytes") as writeProgress:
        # Start at address 0
        byteAddress = 0
        # Seek to the correct position in the file to begin reading from
        dumpFile.seek(byteAddress)
        
        # Loop through every available byte in the input file and flash it from the file
        while (byteAddress < fileSize):
            # Read the max amount of data, or the remaining data (whichever is smaller)
            txCount = min(args.bytesPerPage, (fileSize - byteAddress))

            # Load the correct number of bytes for the tx
            fileData = list(dumpFile.read(txCount))

            # Transmit the write address of the EEPROM, along with the byte position to start writing and the data to write.
            txData = [WRITE_ADDRESS, ((byteAddress >> 8) & 0xFF), (byteAddress & 0xFF)] + fileData

            # Write and then read the specified number of bytes
            rxData = busPirate.write_then_read(len(txData), 0, txData)

            # Calculate the next address to flash
            byteAddress += txCount
            
            # Update progress bar
            writeProgress.update(txCount)

# After the flash is finished, send a stop bit and disable the power supply on the BusPirate
busPirate.stop()
busPirate.configure(power = False)

# After file close, inform the user that the flash completed successfully
print(f"{OutputColours.INFO}[INFO] File flashed to EEPROM successfully.{OutputColours.END}")
