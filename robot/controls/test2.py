import marsutils
import wpilib

from wpilib.interfaces.generichid import GenericHID

from components.drive import DriveMode, Drive
from components import Lift


class Test2(marsutils.ControlInterface):
    """ A bunch of random controls for testing
    """

    _DISPLAY_NAME = "Test 2"

    gamepad: wpilib.XboxController
    gamepad2: wpilib.XboxController

    drive: Drive
    lift: Lift

    def __init__(self):
        self.drive_mode = DriveMode.MECANUM
        super().__init__()

    def teleopPeriodic(self):
        if self.gamepad.getRawButtonPressed(6):  # TODO: Change id
            self.drive_mode = self.drive_mode.toggle()

        if self.drive_mode == DriveMode.MECANUM:
            forward_speed = self.gamepad.getTriggerAxis(GenericHID.Hand.kRight)
            reverse_speed = -self.gamepad.getTriggerAxis(GenericHID.Hand.kLeft)
            total_speed = (
                forward_speed
                + reverse_speed
                + -self.gamepad.getY(GenericHID.Hand.kRight)
            )

            self.drive.drive_mecanum(
                self.gamepad.getX(GenericHID.Hand.kRight),
                total_speed,
                self.gamepad.getX(GenericHID.Hand.kLeft),
            )
        else:
            self.drive.drive_tank(
                -self.gamepad.getY(GenericHID.Hand.kRight),
                self.gamepad.getX(GenericHID.Hand.kLeft),
            )

        self.lift.set_speed(
            -self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft)
            + self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight)
        )
