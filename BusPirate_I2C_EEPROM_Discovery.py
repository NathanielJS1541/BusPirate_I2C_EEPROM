# Import argparse to handle command line arguments and help texts
import argparse

# Import Path from Pathlib to handle directories
from pathlib import Path

# Import the pyBusPirateLite library
from pyBusPirateLite.I2C import I2C, ProtocolError
from pyBusPirateLite.common_functions import *

# Import the tqdm progress bar library
from tqdm import tqdm

# Import termtables to display data as a table
import termtables as tt

# EEPROM Constants
MAXIMUM_MEMORY_ADDRESS = 0xFFFF # These scripts only support 16-bit memory addresses.
MAXIMUM_I2C_ADDRESS = 0xFF      # Scan the entire address space supported by I2C

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
parser.add_argument("-s", "--search",         dest="search",        help="Attempt to discover the addresses of attached I2C devices.",                       action="store_true")
parser.add_argument("-m", "--memory-layout",  dest="memoryLayout",  help=f"Attempt to discover the memory layout of attached EEPROM(S). {OutputColours.WARNING}Warning: Will write to the EEPROM(S).{OutputColours.END}", action="store_true")
parser.add_argument("-a", "--address",        dest="address",       help="The I2C address of the EEPROM module you would like to inspect (For -m only).",    type=auto_int,  required=False)
parser.add_argument("-c", "--clock-speed",    dest="clockSpeed",    help="The clock speed to use when communicating with the EEPROM module.",                type=str,  required=False, default="400kHz", choices=["400kHz", "100kHz", "50kHz", "5kHz"])
parser.add_argument("-e", "--enable-pullups", dest="enablePullups", help="Enable the internal pullup resistors in the BusPirate. Disabled by default.",      action="store_true")
parser.add_argument("-v", "--verbose",        dest="verbose",       help="Print verbose messages.",                                                          action="store_true")

# Parse the user inputs using the argument parser
args = parser.parse_args()
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# Create a busPirate object configured to communicate over I2C
busPirate = I2C()

# Set the I2C clock speed of the BusPirate
busPirate.speed = args.clockSpeed

# Configure the BusPirate's power output and internal pullup resistors
busPirate.configure(power = True, pullup = args.enablePullups)

# If the -s/--search flag is set, scan through all possible I2C addresses and list addresses that responded to I2C commands with an ACK.
if args.search == True:
    # Create a blank array to store the valid addresses in
    foundAddresses = []
    
    # Send a start bit
    busPirate.start()
    # Set up a progress bar to show how many addresses have been scanned
    with tqdm(total = MAXIMUM_I2C_ADDRESS, unit = " addresses") as scanProgress:
        # Loop through every possible address and try to write data to each. (Avoid general call address 0x00, as multiple devices may respond)
        for scanAddress in range(1, MAXIMUM_I2C_ADDRESS + 1):
            # Attempt to write to the current address being scanned
            try:
                busPirate.write_then_read(1, 1, [scanAddress])
                # print(f"{OutputColours.INFO}[INFO] Device found at {scanAddress}.{OutputColours.END}")
                # If an exception is not raised, the device responded and this is a valid address
                foundAddresses += [scanAddress]
            except ProtocolError:
                if args.verbose == True:
                    print(f"{OutputColours.VERBOSE}[VERBOSE] No device found at address {hex(scanAddress)}.{OutputColours.END}")
            
            # Update progress bar
            scanProgress.update(1)
    # Send a stop bit
    busPirate.stop()

    # After the address scan is complete, report this to the user
    print(f"{OutputColours.INFO}[INFO] Address scanning complete.{OutputColours.END}")

    # Sort the addresses into groups of I2C addresses, with the respective read and write addresses
    EEPROM_Addresses = []
    unknownAddresses = []
    for address in foundAddresses:
        # Get the I2C address of the EEPROM (7 most significant bits)
        I2C_Address = (address >> 1) & 0b01111111
        # The read address is the I2C address bit shifted with the LSB set to 1
        readAddress = (I2C_Address << 1) | 0b00000001
        # The read address is the I2C address bit shifted with the LSB set to 0
        writeAddress = (I2C_Address << 1) & 0b11111110
        
        # Check that both a read and write address were found, if not it may not be an EEPROM and we should just report the found address.
        if (readAddress in foundAddresses) and (writeAddress in foundAddresses):
            # Only store these addresses if they have not already been stored
            if [I2C_Address, readAddress, writeAddress] not in EEPROM_Addresses:
                EEPROM_Addresses += [[I2C_Address, readAddress, writeAddress]]
        else:
            print(f"{I2C_Address} - {readAddress} - {writeAddress}")
            unknownAddresses += [address]

    # Display the found devices using termtables if the list isn't empty
    if len(EEPROM_Addresses) != 0:
        print(f"{OutputColours.INFO}[INFO] Found valid Addresses:")
        tt.print(
            [[hex(addr[0]), hex(addr[1]), hex(addr[2])] for addr in EEPROM_Addresses],
            header=["I2C Address", "Read Address", "Write Address"],
            style=tt.styles.rounded_double,
            padding=(0, 1),
            alignment="ccc"
        )
        print(OutputColours.END)
    else:
        print(f"{OutputColours.WARNING}[WARN] No EEPROM addresses were found. Please check your wiring or enable/disable internal pullups.{OutputColours.END}")
    
    # Display a warning if single addresses were found
    if len(unknownAddresses) != 0:
        print(f"{OutputColours.WARNING}[WARN] Devices with only a single address were found:")
        tt.print(
            [[hex(addr)] for addr in unknownAddresses],
            header=["Unknown Addresses"],
            style=tt.styles.rounded_double,
            padding=(0, 1),
            alignment="c"
        )
        print(OutputColours.END)

# After the scan is finished, disable the power supply on the BusPirate
#busPirate.configure(power = False)

# If the -m/--memory-layout flag is set, attempt to discover the memory layout of any attached EEPROM(S)
if args.memoryLayout == True:
    # If no address has been supplied and search has not been disabled
    if args.address == None and args.search == False:
        print(f"{OutputColours.ERROR}[ERR] No EEPROM address was supplied and address search was not enabled. Cannot analyse memory layout.{OutputColours.END}")
    # If search was enabled but no addresses were found, warn user and exit
    elif args.search == True and len(EEPROM_Addresses) == 0:
        print(f"{OutputColours.ERROR}[ERR] Search enabled but no addresses were found. Cannot analyse memory layout.{OutputColours.END}")
    # Otherwise, continue to analyse memory layout
    else:
        print(f"{OutputColours.ERROR}[ERR] Function not implemented.{OutputColours.END}")

# busPirate.disconnect()  # Free up COM port - doesn't seem to work
# Reset the BusPirate to disable all outputs and reset it to "HiZ" mode. Should also free up the COM port.
busPirate.hw_reset()

