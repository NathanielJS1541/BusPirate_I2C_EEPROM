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

# Input Configuration Constants
wiperString = 0x00

# Create a busPirate object configured to communicate over I2C
busPirate = I2C()

# Set the I2C clock speed of the BusPirate
busPirate.speed = '400kHz'

# Configure the BusPirate and enable the power output but disable Pull-Up resistors
busPirate.configure(power = True, pullup=False)

# Start the BusPirate interface
busPirate.start()

# Initialise a progress bar for the write operation
with tqdm(total = totalBytes, unit = " bytes") as writeProgress:
    # Loop through every available byte and read it
    byteAddress = 0 # Start at address 0
    while (byteAddress < totalBytes):
        # Read the max amount of data, or the remaining data (whichever is smaller)
        txCount = min(bytesPerPage, (totalBytes - byteAddress))

        # If txCount == 0, there is no data left to write, so break.
        if txCount == 0:
            break

        # Load the correct number of bytes for the tx
        wiperData = [wiperString] * txCount

        # Transmit the write address of the EEPROM, along with the byte position to start writing and the data to write.
        txData = [WRITE_ADDRESS, ((byteAddress >> 8) & 0x7F), (byteAddress & 0xFF)] + wiperData

        # Write and then read the specified number of bytes
        rxData = busPirate.write_then_read(len(txData), 0, txData)

        # Update progress bar
        writeProgress.update(txCount)

        # Calculate the next address to read from
        byteAddress += txCount


