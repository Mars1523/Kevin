import glob
import sys
import serial


# *nix only, no clue how windows handles serial devices
serial_modem_paths = glob.glob("/dev/cu.usbmodem*")
if len(serial_modem_paths) < 1:
    print("Unable to find usb serial modem")
    sys.exit(1)

serial = serial.Serial(serial_modem_paths[0], 9600)


while True:
    mode = input("> ").strip()
    try:
        serial.write(bytes([int(mode)]))
        serial.flush()
    except:
        pass
