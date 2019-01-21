import marsutils
import wpilib

from wpilib.interfaces.generichid import GenericHID

from ..components.drive import DriveMode, Drive


class Testing(marsutils.ControlInterface):
    """ A bunch of random controls for testing
    """

    _DISPLAY_NAME = "Testing"

    gamepad: wpilib.XboxController

    drive: Drive

    def __init__(self):
        self.drive_mode = DriveMode.MECANUM
        super().__init__()

    def teleopPeriodic(self):
        if self.gamepad.getRawButtonPressed(6):  # TODO: Change id
            self.drive_mode = self.drive_mode.toggle()

        if self.drive_mode == DriveMode.MECANUM:
            self.drive.drive_mecanum(
                self.gamepad.getX(GenericHID.Hand.kLeft),
                -self.gamepad.getY(GenericHID.Hand.kLeft),
                self.gamepad.getX(GenericHID.Hand.kRight),
            )
        else:
            self.drive.drive_tank(
                self.gamepad.getY(GenericHID.Hand.kRight),
                self.gamepad.getX(GenericHID.Hand.kLeft),
            )