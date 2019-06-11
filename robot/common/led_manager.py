import wpilib

from enum import Enum


class LedPattern(Enum):
    Off = 0
    RedFader = 1
    BlueFader = 2
    FastWarning = 4
    Rainbow1 = 7
    Rainbow2 = 8


class LEDManager:
    """
        Communicate with the ardunio leds
    """

    fast: bool = False
    last: LedPattern = LedPattern.Off

    def __init__(self, baud=9600, port=wpilib.SerialPort.Port.kUSB):
        # Don't explode if there is nothing plugged in
        try:
            self.serial = wpilib.SerialPort(baud, port)
        except:
            pass

    def alliance_fader(self):
        try:
            alliance = wpilib.DriverStation.getInstance().getAlliance()
            if alliance == wpilib.DriverStation.Alliance.Red:
                self.write_pattern(LedPattern.RedFader)
            else:
                self.write_pattern(LedPattern.BlueFader)
        except:
            pass

    def set_fast(self, fast: bool):
        if self.fast != fast:
            if fast:
                self.write_pattern_forget(LedPattern.FastWarning)
            else:
                self.write_pattern_forget(self.last)
        self.fast = fast

    def write_pattern(self, pattern: LedPattern):
        self.last = pattern
        self.write_byte(pattern.value)

    def write_pattern_forget(self, pattern: LedPattern):
        self.write_byte(pattern.value)

    def write_byte(self, byte: int):
        assert byte <= 255, "byte must be less than or equal to 255"
        # Don't explode if there is nothing plugged in
        try:
            self.serial.write(bytes([byte]))
        except:
            pass
