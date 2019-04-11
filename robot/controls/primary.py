import marsutils.math
import wpilib
import rev
import navx
import ctre

import wpilib.robotbase
from wpilib.drive.robotdrivebase import RobotDriveBase
from wpilib.interfaces.generichid import GenericHID

from components.drive import DriveMode, Drive
from components import Lift, Intake
from controllers import AlignCargo, AlignTape
from common import LEDManager


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

    # cargo_align_ctrl: AlignCargo
    tape_align_ctrl: AlignTape

    compressor: wpilib.Compressor

    climb_piston: wpilib.DoubleSolenoid

    leg1: ctre.WPI_TalonSRX
    leg2: ctre.WPI_TalonSRX

    leg_drive: rev.CANSparkMax
    # leg1: rev.CANSparkMax
    # leg2: rev.CANSparkMax
    #
    # leg_drive: ctre.WPI_TalonSRX

    led_manager: LEDManager

    def __init__(self):
        self.drive_mode = DriveMode.TANK
        self.slow = False
        self.angle = 0
        self.fod = False
        super().__init__()

    def teleopPeriodic(self):
        # TODO: Fix for bug in wpilib
        wpilib.shuffleboard.Shuffleboard.update()
        self.slow = self.gamepad.getAButton()
        if self.gamepad.getStickButtonPressed(GenericHID.Hand.kRight):
            self.fod = not self.fod

            if self.fod:
                self.gamepad.setRumble(
                    wpilib.interfaces.GenericHID.RumbleType.kLeftRumble, 1
                )

                def stop():
                    self.gamepad.setRumble(
                        wpilib.interfaces.GenericHID.RumbleType.kLeftRumble, 0
                    )

                if wpilib.robotbase.RobotBase.isReal():
                    wpilib.Notifier(stop).startSingle(0.25)

        # self.led_manager.set_fast(self.fast)

        if self.gamepad.getBumperPressed(GenericHID.Hand.kRight):  # TODO: Change id
            self.drive_mode = self.drive_mode.toggle()

        auto = self.gamepad.getBButton()
        self.tape_align_ctrl.set_enabled(auto)

        if not auto:
            if self.drive_mode == DriveMode.MECANUM:
                forward_speed = -self.gamepad.getY(GenericHID.Hand.kRight)

                if self.slow:
                    forward_speed *= 0.75
                # else:
                #     forward_speed *= 0.9

                strafe_mult = 0.76 if self.slow else 1
                # turn_mult = 0.65 if self.slow else 0.75
                turn_mult = 0.65 if self.slow else 0.75

                self.drive.drive_mecanum(
                    self.gamepad.getX(GenericHID.Hand.kRight) * strafe_mult,
                    forward_speed,
                    self.gamepad.getX(GenericHID.Hand.kLeft) * turn_mult,
                    fod=self.fod,
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
            self.lift.set_setpoint(200)
        elif pov == 270:  # Left
            self.lift.set_setpoint(380.5)
        elif pov == 0:  # Up
            self.lift.set_setpoint(1180.5)
        elif pov == 90:  # Right
            self.lift.set_setpoint(2028)  # max

        if self.gamepad2.getYButton():
            self.lift.set_setpoint(575)
        elif self.gamepad2.getXButton():
            self.lift.set_setpoint(420)

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
            self.intake.pid_controller.getSetpoint() - (wrist_setpoint_adj * 15)
        )

        if self.gamepad.getBumperPressed(
            GenericHID.Hand.kLeft
        ) or self.gamepad2.getBumperPressed(GenericHID.Hand.kLeft):
            self.intake.toggle_grab()

        if self.gamepad.getYButton():
            self.drive.zero_fod()

        if self.gamepad.getBackButton():
            self.compressor.stop()

        if self.gamepad.getStartButton():
            self.compressor.start()

        if self.gamepad.getXButton():
            self.climb_piston.set(wpilib.DoubleSolenoid.Value.kReverse)
        else:
            self.climb_piston.set(wpilib.DoubleSolenoid.Value.kForward)

        if self.gamepad2.getAButton():
            self.intake.set_defense()

        leg_speed = -marsutils.math.signed_square(
            (
                self.gamepad.getTriggerAxis(GenericHID.Hand.kRight)
                + -self.gamepad.getTriggerAxis(GenericHID.Hand.kLeft)
            )
        )

        self.leg1.set(leg_speed)
        self.leg2.set(leg_speed)

        if self.gamepad.getXButton():
            # self.leg_drive.set(-self.gamepad.getY(GenericHID.Hand.kRight) * 50)
            self.leg_drive.set(-1)
        else:
            self.leg_drive.set(0)
