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
parser.add_argument("-o", "--output-file",    dest="outputFile",    help="Path to the dump file that will be created by the program.",                       type=Path, required=False, default="./EEPROM_Dump.hex")
parser.add_argument("-e", "--enable-pullups", dest="enablePullups", help="Enable the internal pullup resistors in the BusPirate. Disabled by default.",      action="store_true")
parser.add_argument("-f", "--force",          dest="force",         help="Allow overwrites of the output file if it exists, and create missing directories", action="store_true")
parser.add_argument("-v", "--verbose",        dest="verbose",       help="Print verbose messages.",                                                          action="store_true")

# Parse the user inputs using the argument parser
args = parser.parse_args()
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------ Input Valudation ------------------------------------------------------------------------------------------------
# Just warn the user about using the -f flag when it is not needed
if args.force:
    print(f"{OutputColours.WARNING}[WARN] The {OutputColours.BOLD}-f{OutputColours.END}{OutputColours.WARNING} flag allows the program to overwrite existing files on your system, and recursively create "
          f"directories if you specify a directory that does not exist.\n       Only use it if you understand this.{OutputColours.END}")

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

# Ensure that either the parent directory of the output file exists, or the -f flag has been set
if not args.outputFile.parent.exists() and not args.force:
    # If it doesn't exist and -f has not been specified, print an error message and exit the program without writing anything. User must allow creation of directories.
    raise SystemExit(f"{OutputColours.ERROR}[ERR] The output file parent directory ({args.outputFile.parent}) does not exist, and --force/-f has not been specified.{OutputColours.END}")
elif not args.outputFile.parent.exists() and args.force:
    # If -f was specified and the directory doesn't exist, create it recursively.
    args.outputFile.parent.mkdir(parents=True)

# Ensure either the file doesn't exist, or that the -f flag has been set
if args.outputFile.exists() and args.outputFile.is_file() and not args.force:
    # If it does exist and -f has not been specified, print an error message and exit the program without writing anything. User must explicitly state they wish the file to be overwritten.
    raise SystemExit(f"{OutputColours.ERROR}[ERR] The output file already exists and --force/-f has not been specified.{OutputColours.END}")
elif args.outputFile.is_file() and args.force:
    # If -f was specified and the file exists, just warn that the file will be overwritten. Too late now...
    print(f"{OutputColours.WARNING}[WARN] The existing file {args.outputFile.resolve()} will be overwritten.{OutputColours.END}")
elif args.outputFile.exists() and args.outputFile.is_dir():
    # In this case, it appears as if the specified output is a directory. Warn user and quit.
    raise SystemExit(f"{OutputColours.ERROR}[ERR] The specified output appears to be a directory.{OutputColours.END}")
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Create a busPirate object configured to communicate over I2C
busPirate = I2C()

# Set the I2C clock speed of the BusPirate
busPirate.speed = args.clockSpeed

# Configure the BusPirate's power output and internal pullup resistors
busPirate.configure(power = True, pullup = args.enablePullups)

# Send a start bit
busPirate.start()

# Initialise the output file and a progress bar for the write operation
with open(args.outputFile, "wb") as dumpFile:
    with tqdm(total = totalBytes, unit = " bytes") as readProgress:
        # Start at address 0
        byteAddress = 0
        
        # Loop through every available byte in the EEPROM and dump it to a file
        while (byteAddress < totalBytes):
            # Set the EEPROM address for a sequential read.
            busPirate.transfer([WRITE_ADDRESS, ((byteAddress >> 8) & 0x7F), (byteAddress & 0xFF) ])

            # Read the max amount of data, or the remaining data (whichever is smaller)
            rxCount = min(args.bytesPerPage, (totalBytes - byteAddress))

            # The only data to be written is the read address of the EEPROM
            txData = [READ_ADDRESS]
            # Write and then read the specified number of bytes
            rxData = busPirate.write_then_read(len(txData), rxCount, txData)

            # If the read was successful, write the contents to a file
            dumpFile.write(rxData)

            # Calculate the next address to read from
            byteAddress += rxCount
            
            # Update progress bar
            readProgress.update(rxCount)

# After the dump is finished, send a stop bit and disable the power supply on the BusPirate
busPirate.stop()
busPirate.configure(power = False)

# After file close, inform the user that the dump completed successfully
print(f"{OutputColours.INFO}[INFO] File written to {args.outputFile.resolve()}.{OutputColours.END}")

