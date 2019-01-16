import marsutils
import wpilib

from wpilib.interfaces.generichid import GenericHID

from .. import components


class Testing(marsutils.ControlInterface):
    """ A bunch of random controls for testing
    """

    _DISPLAY_NAME = "Testing"

    gamepad: wpilib.XboxController

    drive: components.Drive

    def teleopPeriodic(self):
        self.drive.drive_tank(
            self.gamepad.getY(GenericHID.Hand.kRight),
            self.gamepad.getX(GenericHID.Hand.kLeft),
        )
