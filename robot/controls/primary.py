import marsutils
import marsutils.math
import wpilib
import navx

from wpilib.interfaces.generichid import GenericHID

from components.drive import DriveMode, Drive
from components import Lift, Intake


class Primary(marsutils.ControlInterface):
    """
        Primary control, uses 2 xbox gamepads
    """

    _DISPLAY_NAME = "Primary"

    gamepad: wpilib.XboxController
    gamepad2: wpilib.XboxController

    navx: navx.AHRS

    drive: Drive
    lift: Lift
    intake: Intake

    def __init__(self):
        self.drive_mode = DriveMode.TANK
        super().__init__()

    def teleopPeriodic(self):
        # TODO: Fix for bug in wpilib
        wpilib.shuffleboard.Shuffleboard.update()
        if self.gamepad.getRawButtonPressed(6):  # TODO: Change id
            self.drive_mode = self.drive_mode.toggle()

            self.navx.setAngleAdjustment(self.navx.getAngle())

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
        pov = self.gamepad2.getPOV()
        if pov == 180:  # Down (Minimum)
            self.lift.set_setpoint(0)
        elif pov == 270:  # Left
            self.lift.set_setpoint(1025)
        elif pov == 0:  # Up
            self.lift.set_setpoint(2150)

        setpoint = self.lift.get_setpoint()
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) > 0.02:
            self.lift.set_setpoint(
                setpoint + (self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) * 70)
            )
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) > 0.02:
            self.lift.set_setpoint(
                setpoint - (self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) * 70)
            )

        self.intake.set_speed(-self.gamepad2.getY(GenericHID.Hand.kLeft))
        self.intake.set_wrist(
            RobotDriveBase.applyDeadband(
                self.gamepad2.getY(GenericHID.Hand.kRight), 0.01
            )
        )

        self.intake.set_speed(self.gamepad2.getY(GenericHID.Hand.kLeft))
        self.intake.set_wrist(self.gamepad2.getY(GenericHID.Hand.kRight))
        if self.gamepad2.getXButton():
            self.intake.extend_piston()
        else:
            self.intake.retract_piston()
