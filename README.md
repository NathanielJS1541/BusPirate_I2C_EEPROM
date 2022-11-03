# BusPirate_I2C_EEPROM
These Python scripts are intended to make reading/writing large amounts of data to I2C EEPROM chips with a [BusPirate](http://dangerousprototypes.com/docs/Bus_Pirate) much easier. I 
have found that tools like [flashrom](https://github.com/flashrom/flashrom) work really well for SPI EEPROM chips, but there don't really seem to be any programs that allow the 
same functionality for I2C EEPROM chips.

## Tested EEPROM Chips
This list will be expanded as I get my hands on more EEPROM chips, but these scripts will be initially developed for the ATMEL 24C256 as it's what I have on hand. Datasheets 
for the chips I have tested will be in the **Datasheets** directory.
- ATMEL 24C256

## Requirements
- Python3.6+, since I rely (maybe too much) on f-strings, as do some libraries.
- [pyBusPirateLite](https://github.com/juhasch/pyBusPirateLite)
  - Just clone this repo somewhere and run `python ./setup.py install` from in the repo to install the library and its dependencies.
- [tqdm](https://github.com/tqdm/tqdm)
- A [BusPirate](http://dangerousprototypes.com/docs/Bus_Pirate)

## Basic Wiring Diagram
|               BusPirate               | EEPROM Chip |
|:-------------------------------------:|:-----------:|
| +5V or 3V3 (Depending on your EEPROM) |     VCC     |
|                  CLK                  |     SCL     |
|                  MOSI                 |     SDA     |
|                  GND                  |     GND     |

## Script Usage
The scripts can be run with `python ./script-name.py`. Currently all variables are hard-coded into the scripts while I test the concepts, so edit the scripts and change as necessary.
- **Blank_Dump_Creator.py** is used to create a .hex file filled with a byte of your choosing. This can be used to help verify the flasher, dumper and wiper script.
- **BusPirate_I2C_EEPROM_Dump.py** is used to dump everything from the EEPROM chip into a single binary file (.hex by default).
- **BusPirate_I2C_EEPROM_Flash.py** is used to upload a binary dump file (.hex by default) to the EEPROM chip.
- **BusPirate_I2C_EEPROM_Wipe.py** completely fills the EEPROM chip with a chosen byte to remove other data.
