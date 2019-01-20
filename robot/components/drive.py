import wpilib
import wpilib.drive
from enum import Enum, auto


class DriveMode(Enum):
    MECANUM = auto()
    TANK = auto()

    def toggle(self):
        if self == self.MECANUM:
            return self.TANK
        else:
            return self.MECANUM


class Drive:
    """
        Kevin has a high power drive train that uses
        mecanum and tank (Octocanum) to provide
        maneuverability and power
    """

    tank_drive: wpilib.drive.DifferentialDrive
    mecanum_drive: wpilib.drive.MecanumDrive

    octacanum_shifter: wpilib.DoubleSolenoid

    # front_left_enc: CANTalonEncoder
    # front_right_enc: CANTalonEncoder
    # rear_left_enc: CANTalonEncoder
    # rear_right_enc: CANTalonEncoder

    def __init__(self):
        # Current drive mode, this changes when a control calls its drive function
        self.drive_mode = DriveMode.TANK

        # Rotation, negative turns to the left, also known as z
        # Used for both
        self.rotation = 0
        # Speed, positive is positive (joystick must be inverted)
        # Used for both
        self.y = 0
        # Horizontal speed
        # Mecanum only
        self.x = 0

    def drive_mecanum(self, y, x, z):
        self.rotation = z
        self.y = y
        self.x = x

        self.drive_mode = DriveMode.MECANUM

    def drive_tank(self, y, z):
        self.rotation = z
        self.y = y

        self.drive_mode = DriveMode.TANK

    def set_mode(self, mode: DriveMode):
        self.drive_mode = mode

    def execute(self):
        # feed the other drive train to appease the motor safety
        if self.drive_mode == DriveMode.TANK:
            self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kForward)
            self.tank_drive.arcadeDrive(self.y, self.rotation)
            self.mecanum_drive.feed()
        elif self.drive_mode == DriveMode.MECANUM:
            self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kReverse)
            self.mecanum_drive.driveCartesian(self.y, self.x, self.rotation)
            self.tank_drive.feed()

        self.x = 0
        self.y = 0
        self.rotation = 0

    def reset_encoders(self):
        """ Reset all associated encoders
        """
        pass
        # self.front_left_enc.zero()
        # self.front_right_enc.zero()
        # self.rear_left_enc.zero()
        # self.rear_right_enc.zero()
