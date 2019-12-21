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


## This class contains the code to drive kevin, and inherts `marsutils.ControlInterface`
## so that it is detected by `@with_ctrl_manager` magic
class Primary(marsutils.ControlInterface):
    """
        Primary control, uses 2 xbox gamepads
    """

    ## This is the name that `@with_ctrl_manager` will display on the dashboard
    ## it is prefixed with an underscore so it is ignored by magicbot
    _DISPLAY_NAME = "Primary"

    ## See `components.drive.Drive` for an explanation of these variables
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

    ## Define the "state", or the data we want to track between ticks to the periodic
    ## functions
    ##
    ## Components usually define this sort of thing in `setup()`, and this probably
    ## should too.
    def __init__(self):
        self.drive_mode = DriveMode.TANK
        self.slow = False
        self.angle = 0
        self.fod = False
        super().__init__()

    ## This is one of the robot lifecycle functions, and is called repetedly (60hz)
    ## while the robot is enabled in teleop mode
    ## In this function, we gather inputs from controllers and use that data
    ## to control the various components of the robot
    def teleopPeriodic(self):
        # TODO: Fix for bug in wpilib (this shouldn't be needed anymore)
        wpilib.shuffleboard.Shuffleboard.update()

        ## The gamepad `.get[SomeButton]()` functions provide the
        ## _current_ state of the button, as in "is it pressed right now or not?"
        ## there are also `.get[SomeButton]Pressed()` functions which check if
        ## the button has been pressed since the last time you checked.
        ## This is useful for toggles because it's pretty hard to only press the
        ## button for 1/60th of a second
        ## https://robotpy.readthedocs.io/projects/wpilib/en/latest/wpilib/XboxController.html
        ## In this case, wheteher or not we are slow should be decided by the
        ## current state of the button.
        # Drive
        self.slow = self.gamepad.getAButton()

        ## This is a toggle, so we use a ".get[SomeButton]Pressed()" function.
        # Toggle field-oriented-drive with the right stick button
        if self.gamepad.getStickButtonPressed(GenericHID.Hand.kLeft):
            ## This inverts the value of `self.fod`
            self.fod = not self.fod

            if self.fod:
                ## Provide some haptic feedback that the robot is now in FOD
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

        ## Only process human input if not auto controllers are trying to drive
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
        ## Gamepad pov buttons are reported in degrees, with zero at the top
        ## and -1 when nothing is pressed.
        ## These are the lift presets, which allow the driers to quickly
        ## bring the lift to predefined heights useful in the game.
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

        ## We want the stick to define how fast we change the setpoint, not set
        ## it's position directly.
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

        ## Unlike the wrist, we just set the motors percent ouput to be equal to
        ## how much the stick has been moved
        ## (I didn't get enough time to PID this too...)
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
            ## Controlling the robot drive train, legs, pistons, and wheel speeds
            ## proved to require more fingers than our primary driver had,
            ## so we just set the leg wheels to drive backward.  We don't need
            ## to climb down,  if we need to do that we just floor it and hope for
            ## the best.
            self.climb.set_drive_speed(-1)
        else:
            self.climb.set_drive_speed(0)
