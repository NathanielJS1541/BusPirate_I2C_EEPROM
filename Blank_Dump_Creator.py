# Import argparse to handle command line arguments and help texts
import argparse

# Import Path from Pathlib to handle directories
from pathlib import Path

# Import the tqdm progress bar library
from tqdm import tqdm

# EEPROM Constants
MAXIMUM_MEMORY_ADDRESS = 0xFFFF  # These scripts only support 16-bit memory addresses.

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

# ----------------------------------------------------------------------------------------------- Argument Parser ------------------------------------------------------------------------------------------------
# Set up the argument parser to retreive inputs from the user
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-b", "--bytes-per-page", dest="bytesPerPage", help="The number of bytes per page listed in the EEPROM datasheet.",                     type=int,  required=True)
parser.add_argument("-p", "--total-pages",    dest="totalPages",   help="The number of memory pages listed in the EEPROM datasheet.",                       type=int,  required=True)
parser.add_argument("-s", "--hexstring",      dest="hexString",    help="A string of hex characters that will be used to output to the dump file.",         type=str,  required=False, default="DEADBEEF")
parser.add_argument("-o", "--output-file",    dest="outputFile",   help="Path to the dump file that will be created by the program.",                       type=Path, required=False, default="./Blank_Dump.hex")
parser.add_argument("-f", "--force",          dest="force",        help="Allow overwrites of the output file if it exists, and create missing directories", action="store_true")
parser.add_argument("-v", "--verbose",        dest="verbose",      help="Print verbose messages.",                                                          action="store_true")

# Parse the user inputs using the argument parser
args = parser.parse_args()
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------- Input Valudation -----------------------------------------------------------------------------------------------
# Just warn the user about using the -f flag when it is not needed
if args.force:
    print(f"{OutputColours.WARNING}[WARN] The {OutputColours.BOLD}-f{OutputColours.END}{OutputColours.WARNING} flag allows the program to overwrite existing files on your system, and recursively create "
          f"directories if you specify a directory that does not exist.\n       Only use it if you understand this.{OutputColours.END}")

# Calculate the total number of bytes to generate
totalBytes = args.bytesPerPage * args.totalPages

# Ensure that the specified file can be writted to a device with 16-bit addresses, as this is what the other scripts here support.
if totalBytes > MAXIMUM_MEMORY_ADDRESS:
    raise ValueError(f"{OutputColours.ERROR}[ERR] These scripts can operate with up to 16-bit memory addresses. The maximum possible address is {MAXIMUM_MEMORY_ADDRESS}, but up to address {totalBytes} was "
                     f"requested. Consider lowering the pages (-p) value.{OutputColours.END}")

# Convert the hex string into an immutable array of bytes
dumpString = bytes.fromhex(args.hexString)
dumpStringBytes = len(dumpString)

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
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Initialise the output file and a progress bar for the write operation
with open(args.outputFile, "wb") as dumpFile:
    with tqdm(total = totalBytes, unit = " bytes") as writeProgress:
        # Start at address 0
        byteAddress = 0

        # Sequentially write to the file
        while (byteAddress < totalBytes):
            # Calculate the number of bytes to write. This is either the full length of the dumpString, or the remaining amount of bytes to fill the EEPROM; whichever is smaller.
            bytesToWrite = min(dumpStringBytes, (totalBytes - byteAddress))

            # Write the number of bytes calculated from the string.
            dumpFile.write(dumpString[0:bytesToWrite])

            # Update the value of byte address to reflect how many bytes have been written.
            byteAddress += bytesToWrite

            # Update progress bar
            writeProgress.update(bytesToWrite)

# After file close, inform the user that the write completed successfully
print(f"{OutputColours.INFO}[INFO] File written to {args.outputFile.resolve()}.")

