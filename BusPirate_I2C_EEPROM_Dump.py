# Import the pyBusPirateLite library
from pyBusPirateLite.I2C import I2C

# Import the tqdm progress bar library
from tqdm import tqdm

# Library Constants
MaxDataTransfer = 16  # The pyBusPirate library transfer function can transfer 16 bytes maximum (Not including 1 byte for the address)
MaxRxTxBytes = 4096   # The maximum number of bytes that can be transmitted by the write_then_read function

# EEPROM Configuration constants
bytesPerPage = 64
totalPages = 512
totalBytes = bytesPerPage * totalPages
I2C_ADDRESS = 0x50                               # This is the 7 most significant bits of the address, as the least significant bit denotes read (1) or write (0) mode.
WRITE_ADDRESS = (I2C_ADDRESS << 1) & 0b11111110  # The EEPROM write address is the I2C_ADDRESS but bit shifted and with a 0 in the LSB
READ_ADDRESS = (I2C_ADDRESS << 1) | 0b00000001   # The EEPROM read address is the I2C_ADDRESS but bit shifted and with a 1 in the LSB

# Output Configuration Constants
outputFileName = "EEPROM_Dump.hex"

# Create a busPirate object configured to communicate over I2C
busPirate = I2C()

# Set the I2C clock speed of the BusPirate
busPirate.speed = '400kHz'

# Configure the BusPirate and enable the power output but disable Pull-Up resistors
busPirate.configure(power = True, pullup=False)

# Start the BusPirate interface
busPirate.start()

# Initialise a progress bar for the read operation
with open(outputFileName, "wb") as dumpFile:
    with tqdm(total = totalBytes, unit = " bytes") as readProgress:
        # Loop through every available byte and read it
        byteAddress = 0 # Start at address 0
        while (byteAddress < totalBytes):
            # Set the EEPROM address for a sequential read.
            busPirate.transfer([WRITE_ADDRESS, ((byteAddress >> 8) & 0x7F), (byteAddress & 0xFF) ])

            # Read the max amount of data, or the remaining data (whichever is smaller)
            rxCount = min(bytesPerPage, (totalBytes - byteAddress))

            # If rxCount == 0, there is no data left to read, so break.
            if rxCount == 0:
                #print(f"Last address reached: {byteAddress}")
                break

            # The only data to be written is the read address of the EEPROM
            txData = [READ_ADDRESS]
            # Write and then read the specified number of bytes
            rxData = busPirate.write_then_read(len(txData), rxCount, txData)

            # If the read was successful, write the contents to a file
            dumpFile.write(rxData)

            # Update progress bar
            readProgress.update(rxCount)

            # Calculate the next address to read from
            byteAddress += rxCount


