import wpilib
import wpilib.drive
from enum import Enum, auto
import math
import marsutils.math
import navx
from magicbot import will_reset_to

from common.encoder import BaseEncoder


## This is a simple enumeration (it can be one or the other),
## to track whether we are in mecanum or tank mode with a helper function to
## toggle the state.
class DriveMode(Enum):
    MECANUM = auto()
    TANK = auto()

    def toggle(self):
        if self == self.MECANUM:
            return self.TANK
        else:
            return self.MECANUM


## This is a magicbot component, they are not required to inhert any class (but
## they can if needed)
## They define the variables they need and magicbot magic takes care of the rest.
## Every "tick" (when there is new control data, about 60 times per second),
## magicbot calls every components' `execute()` function, whose purpose is to
## apply the current state (stored in variables) and apply it to the robot (by
## setting motor speeds and such).
## An important part of the magicbot component system is that no other function
## should have any effect on the "real world", only execute.  In other words, all,
## other function should only change variables.
##
## Setup code (like defining default state) should go in the `setup()` function
##
## https://robotpy.readthedocs.io/projects/utilities/en/latest/magicbot.html#module-magicbot.magiccomponent
class Drive:
    """
        Kevin has a high power drive train that uses
        mecanum and tank (Octocanum) to provide
        maneuverability and power
    """

    ## These are the "dependent objects" for this component.
    ## Any variables declared here will be detected by magicbot
    ## and at startup, it will look for any variables defined in `Kevin.createObjects()`
    ## and will "wire" them here so they can be used
    tank_drive: wpilib.drive.DifferentialDrive
    mecanum_drive: wpilib.drive.MecanumDrive

    octacanum_shifter_front: wpilib.DoubleSolenoid
    octacanum_shifter_rear: wpilib.DoubleSolenoid

    navx: navx.AHRS

    fl_drive_encoder: BaseEncoder
    fr_drive_encoder: BaseEncoder
    rl_drive_encoder: BaseEncoder
    rr_drive_encoder: BaseEncoder

    ## This is where the default state is defined, and is called only once when the
    ## robot turns on.
    ## `will_reset_to` is a handy utility that makes a special value that will
    ## automagically reset to it's inital value when `execute()` finishes.
    ## This is useful if you have multiple functions that set variables, and might
    ## not always update all the variables (such as drive_mecanum() and drive_tank(),
    ## which causes `self.x` to not always be updated, but `will_reset_to()` handles
    ## that for us).
    ##
    ## I know I said setup code should be in `setup()`... this should be changed...
    def __init__(self):
        # Current drive mode, this changes when a control calls its drive function
        self.drive_mode = will_reset_to(DriveMode.TANK)

        # Rotation, negative turns to the left, also known as z
        # Used for both
        self.rotation = will_reset_to(0)
        # Speed, positive is forward (joystick must be inverted)
        # Used for both
        self.y = will_reset_to(0)
        # Horizontal speed
        # Mecanum only
        self.x = will_reset_to(0)

        self.fod = will_reset_to(False)
        self.adjusted = will_reset_to(True)

    def drive_mecanum(self, y, x, z, fod=False, adjusted=True):
        self.rotation = z
        self.y = y
        self.x = x

        self.fod = fod
        self.adjusted = adjusted

        self.drive_mode = DriveMode.MECANUM

    def drive_tank(self, y, z, adjusted=True):
        self.rotation = z
        self.y = y

        self.adjusted = adjusted

        self.drive_mode = DriveMode.TANK

    def set_mode(self, mode: DriveMode):
        self.drive_mode = mode

    def zero_fod(self):
        """
        Zero the field oriented drive,

        makes the current facing direction "forward"
        """
        self.navx.zeroYaw()

    def execute(self):
        if self.adjusted:
            rot = marsutils.math.signed_square(self.rotation * 0.85)
            # cube the inputs because the drive train is incredibly touchy even at small inputs
            y = math.pow(self.y, 3)
            x = math.pow(self.x, 3)
        else:
            rot = self.rotation
            y = self.y
            x = self.x
        if self.drive_mode == DriveMode.TANK:
            self.octacanum_shifter_front.set(wpilib.DoubleSolenoid.Value.kForward)
            self.octacanum_shifter_rear.set(wpilib.DoubleSolenoid.Value.kForward)
            # We cube the inputs above
            self.tank_drive.arcadeDrive(y, rot, squareInputs=False)
            # feed the other drive train to appease the motor safety
            self.mecanum_drive.feed()
        elif self.drive_mode == DriveMode.MECANUM:
            self.octacanum_shifter_front.set(wpilib.DoubleSolenoid.Value.kReverse)
            self.octacanum_shifter_rear.set(wpilib.DoubleSolenoid.Value.kReverse)
            if self.fod:
                ## WPILib makes FOD really simple, we just need to tell it our
                ## current rotation, and it does the vector math to drive the robot
                ## in the right direction.
                self.mecanum_drive.driveCartesian(
                    y, x, rot, gyroAngle=self.navx.getAngle()
                )
            else:
                self.mecanum_drive.driveCartesian(y, x, rot)
            # feed the other drive train to appease the motor safety
            self.tank_drive.feed()

    def reset_encoders(self):
        """ Reset all drive encoders
        """
        self.fl_drive_encoder.zero()
        self.fr_drive_encoder.zero()
        self.rl_drive_encoder.zero()
        self.rr_drive_encoder.zero()
