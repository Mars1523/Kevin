import wpilib
import wpilib.drive
from enum import Enum, auto
import math
import navx
import marsutils.math

from common.encoder import BaseEncoder


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

    navx: navx.AHRS

    fl_drive_encoder: BaseEncoder
    fr_drive_encoder: BaseEncoder
    rl_drive_encoder: BaseEncoder
    rr_drive_encoder: BaseEncoder

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

        self.limited_pos_y = 0
        self.limited_neg_y = 0
        self.limited_pos_x = 0
        self.limited_neg_x = 0
        self.limit_y = 0.2
        self.limit_x = 0.15

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
        rot = math.pow(self.rotation, 3)
        y = self.ramp_y(math.pow(self.y, 3))
        x = self.ramp_x(math.pow(self.x, 3))
        # feed the other drive train to appease the motor safety
        if self.drive_mode == DriveMode.TANK:
            self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kForward)
            # We cube the inputs above
            self.tank_drive.arcadeDrive(y, rot, squareInputs=False)
            self.mecanum_drive.feed()
        elif self.drive_mode == DriveMode.MECANUM:
            self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kReverse)
            self.mecanum_drive.driveCartesian(y, x, rot)
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

    # Simple ramp
    def ramp_y(self, y):
        if y > 0:
            change_y = y - self.limited_pos_y
            if change_y > self.limit_y:
                change_y = self.limit_y
            elif change_y < -self.limit_y:
                change_y = -self.limit_y
            self.limited_pos_y += change_y
            self.limited_neg_y = 0
            return self.limited_pos_y
        else:
            change_y = y - self.limited_neg_y
            if change_y > self.limit_y:
                change_y = self.limit_y
            elif change_y < -self.limit_y:
                change_y = -self.limit_y
            self.limited_neg_y += change_y
            self.limited_pos_y = 0
            return self.limited_neg_y

    def ramp_x(self, x):
        if x > 0:
            change_x = x - self.limited_pos_x
            if change_x > self.limit_x:
                change_x = self.limit_x
            elif change_x < -self.limit_x:
                change_x = -self.limit_x
            self.limited_pos_x += change_x
            self.limited_neg_x = 0
            return self.limited_pos_x
        else:
            change_x = x - self.limited_neg_x
            if change_x > self.limit_x:
                change_x = self.limit_x
            elif change_x < -self.limit_x:
                change_x = -self.limit_x
            self.limited_neg_x += change_x
            self.limited_pos_x = 0
            return self.limited_neg_x
