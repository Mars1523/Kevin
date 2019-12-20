import marsutils.math
import wpilib
import navx

import wpilib.robotbase
from wpilib.drive.robotdrivebase import RobotDriveBase
from wpilib.interfaces.generichid import GenericHID

from components.drive import DriveMode, Drive
from components import Lift, Intake, Climb
from controllers import AlignCargo, AlignTape
from common import LEDManager, rumble


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
    climb: Climb

    # cargo_align_ctrl: AlignCargo
    tape_align_ctrl: AlignTape

    compressor: wpilib.Compressor

    led_manager: LEDManager

    def __init__(self):
        self.drive_mode = DriveMode.TANK
        self.slow = False
        self.angle = 0
        self.fod = False
        super().__init__()

    def teleopPeriodic(self):
        # TODO: Fix for bug in wpilib (this shouldn't be needed anymore)
        wpilib.shuffleboard.Shuffleboard.update()

        # Drive
        self.slow = self.gamepad.getAButton()

        # Toggle field-oriented-drive with the right stick button
        if self.gamepad.getStickButtonPressed(GenericHID.Hand.kLeft):
            self.fod = not self.fod

            if self.fod:
                rumble.rumble(
                    self.gamepad,
                    duration=0.25,
                    kind=wpilib.interfaces.GenericHID.RumbleType.kLeftRumble,
                )

        # self.led_manager.set_fast(self.fast)

        if self.gamepad.getBumperPressed(GenericHID.Hand.kLeft):
            self.drive_mode = self.drive_mode.toggle()

        # enable auto target seeking
        auto = self.gamepad.getBButton()
        self.tape_align_ctrl.set_enabled(auto)

        if not auto:
            if self.drive_mode == DriveMode.MECANUM:
                forward_speed = -self.gamepad.getY(GenericHID.Hand.kLeft)

                if self.slow:
                    forward_speed *= 0.75
                # else:
                #     forward_speed *= 0.9

                strafe_mult = 0.76 if self.slow else 1
                # turn_mult = 0.65 if self.slow else 0.75
                # Reduce the turn input even without slow mode because Kevin is *really fast*
                turn_mult = 0.65 if self.slow else 0.75

                self.drive.drive_mecanum(
                    self.gamepad.getX(GenericHID.Hand.kLeft) * strafe_mult,
                    forward_speed,
                    self.gamepad.getX(GenericHID.Hand.kRight) * turn_mult,
                    fod=self.fod,
                )
            else:
                if self.slow:
                    self.drive.drive_tank(
                        -self.gamepad.getY(GenericHID.Hand.kLeft) * 0.75,
                        self.gamepad.getX(GenericHID.Hand.kRight) * 0.75,
                    )
                else:
                    self.drive.drive_tank(
                        -self.gamepad.getY(GenericHID.Hand.kLeft),
                        self.gamepad.getX(GenericHID.Hand.kRight),
                    )

        # Lift
        # Presets are disabled because they are dangerous
        # pov = self.gamepad2.getPOV()
        # if pov == 180:  # Down (lowest rocket hatch height)
        #     self.lift.set_setpoint(200)
        # elif pov == 270:  # Left
        #     self.lift.set_setpoint(380.5)
        # elif pov == 0:  # Up
        #     self.lift.set_setpoint(1180.5)
        # elif pov == 90:  # Right
        #     self.lift.set_setpoint(2028)  # max
        #
        # if self.gamepad2.getYButton():
        #     self.lift.set_setpoint(575)
        # elif self.gamepad2.getXButton():
        #     self.lift.set_setpoint(420)

        # manual adjustment of the setpoint with analog triggers
        setpoint = self.lift.get_setpoint()
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) > 0.02:
            self.lift.set_setpoint(
                setpoint + (self.gamepad2.getTriggerAxis(GenericHID.Hand.kRight) * 85)
            )
        if self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) > 0.02:
            self.lift.set_setpoint(
                setpoint - (self.gamepad2.getTriggerAxis(GenericHID.Hand.kLeft) * 85)
            )

        # Intake
        self.intake.set_speed(-self.gamepad2.getY(GenericHID.Hand.kLeft))

        wrist_setpoint_adj = RobotDriveBase.applyDeadband(
            self.gamepad2.getY(GenericHID.Hand.kRight) * 0.5, 0.15
        )

        self.intake.set_wrist_setpoint(
            self.intake.pid_controller.getSetpoint() - (wrist_setpoint_adj * 15)
        )

        if self.gamepad.getBumperPressed(
            GenericHID.Hand.kLeft
        ) or self.gamepad2.getBumperPressed(GenericHID.Hand.kLeft):
            self.intake.toggle_grab()

        # Misc
        if self.gamepad.getYButton():
            self.drive.zero_fod()

        if self.gamepad.getBackButton():
            self.compressor.stop()

        if self.gamepad.getStartButton():
            self.compressor.start()

        if self.gamepad2.getAButton():
            self.intake.set_defense()

        # Climb

        if self.gamepad.getXButton():
            self.climb.extend_piston()
        else:
            self.climb.retract_piston()

        leg_speed = -marsutils.math.signed_square(
            (
                self.gamepad.getTriggerAxis(GenericHID.Hand.kRight)
                + -self.gamepad.getTriggerAxis(GenericHID.Hand.kLeft)
            )
        )

        # The "knee", moves the legs down
        self.climb.set_knee_speed(leg_speed)

        # The leg's wheels
        if self.gamepad.getXButton():
            self.climb.set_drive_speed(-1)
        else:
            self.climb.set_drive_speed(0)
