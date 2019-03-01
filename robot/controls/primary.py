import marsutils.math
import wpilib
import navx
from wpilib.drive.robotdrivebase import RobotDriveBase

from wpilib.interfaces.generichid import GenericHID

from components.drive import DriveMode, Drive
from components import Lift, Intake
from controllers import AlignCargo


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

    cargo_align_ctrl: AlignCargo

    compressor: wpilib.Compressor

    def __init__(self):
        self.drive_mode = DriveMode.TANK
        self.slow = False
        self.angle = 0
        super().__init__()

    def teleopPeriodic(self):
        # TODO: Fix for bug in wpilib
        wpilib.shuffleboard.Shuffleboard.update()
        self.slow = self.gamepad.getAButton()

        if self.gamepad.getRawButtonPressed(6):  # TODO: Change id
            self.drive_mode = self.drive_mode.toggle()

        auto = self.gamepad.getBButton()
        self.cargo_align_ctrl.set_enabled(auto)

        if not auto:
            if self.drive_mode == DriveMode.MECANUM:
                forward_speed = self.gamepad.getTriggerAxis(GenericHID.Hand.kRight)
                reverse_speed = -self.gamepad.getTriggerAxis(GenericHID.Hand.kLeft)
                total_speed = (
                    forward_speed
                    + reverse_speed
                    + -self.gamepad.getY(GenericHID.Hand.kRight)
                )

                if self.slow:
                    total_speed *= 0.75
                else:
                    # total_speed *= 0.9
                    pass

                if self.gamepad.getYButton():
                    pov = self.gamepad.getPOV()
                    if pov == 0:  # Forward
                        self.angle = 0
                    elif pov == 90:  # Right
                        self.angle = 270
                    elif pov == 180:  # Back
                        self.angle = 180
                    elif pov == 270:  # Left
                        self.angle = 90

                strafe_mult = 0.65 if self.slow else 1
                turn_mult = 0.65 if self.slow else 0.75

                self.drive.drive_mecanum(
                    self.gamepad.getX(GenericHID.Hand.kRight) * strafe_mult,
                    total_speed,
                    self.gamepad.getX(GenericHID.Hand.kLeft) * turn_mult,
                    angle=self.angle,
                )
            else:
                if self.slow:
                    self.drive.drive_tank(
                        -self.gamepad.getY(GenericHID.Hand.kRight) * 0.75,
                        self.gamepad.getX(GenericHID.Hand.kLeft) * 0.75,
                    )
                else:
                    self.drive.drive_tank(
                        -self.gamepad.getY(GenericHID.Hand.kRight),
                        self.gamepad.getX(GenericHID.Hand.kLeft),
                    )

        pov = self.gamepad2.getPOV()
        if pov == 180:  # Down (Minimum)
            self.lift.set_setpoint(0)
        elif pov == 270:  # Left
            self.lift.set_setpoint(464.5)
        elif pov == 0:  # Up
            self.lift.set_setpoint(1230.5)
        elif pov == 90:  # Right
            self.lift.set_setpoint(2028)  # max

        setpoint = self.lift.get_setpoint()
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) > 0.02:
            self.lift.set_setpoint(
                setpoint + (self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) * 85)
            )
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) > 0.02:
            self.lift.set_setpoint(
                setpoint - (self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) * 85)
            )

        self.intake.set_speed(-self.gamepad2.getY(GenericHID.Hand.kLeft))

        wrist_setpoint_adj = RobotDriveBase.applyDeadband(
            self.gamepad2.getY(GenericHID.Hand.kRight) * 0.5, 0.15
        )

        self.intake.set_wrist_setpoint(
            self.intake.pid_controller.getSetpoint() + (wrist_setpoint_adj * 7)
        )

        if self.gamepad2.getXButton():
            self.intake.extend_piston()
        else:
            self.intake.retract_piston()

        if self.gamepad2.getYButtonPressed():
            self.intake.toggle_grab()

        if self.gamepad.getBackButton():
            self.compressor.stop()

        if self.gamepad.getStartButton():
            self.compressor.start()
