import magicbot
import wpilib
import wpilib.drive
from wpilib.shuffleboard import Shuffleboard
import rev
import ctre
import navx
from marsutils import with_ctrl_manager, with_setup
from networktables import NetworkTables

from components import Drive, Lift, Intake, Climb
from controllers import AlignCargo, AlignTape
from common.encoder import SparkMaxEncoder, CANTalonQuadEncoder, ExternalEncoder
from common.srx_mag_encoder import AbsoluteMagneticEncoder
from common import LEDManager, rumble
from controls import Primary

from wpilib.interfaces.generichid import GenericHID


## This is the main class of the robot and defines all the components used  (drive, lift, etc),
## the "objects" used by those components (fl_drive motor, leg1 motor, encoders, etc), as
## well as "lifecycle" functions that are called at certain times during the robots life
## such as `teleopInit()`, `autonomous()`, and `disabledInit()` for example

# Order matters
## The @with_setup decorator is a `marsutils` hack that hijacks the magicbot code and calls a special `setup`
## function right after `createObjects()` has been called and the components have been
## "wired" to their objects
@with_setup
## The @with_ctrl_manager decorator (also from `marsutils`) is useful when there are multiple drivers
## and each wants a different control scheme.  Any magic components registered in the main class
## that inherit `marsutils.ControlInterface` are considered "control interfaces" and
## all control code can be written there.
## Kevin however only has one control interface (`controls.primary`), so it's not particulary useful,
## but it is still kind of nice to move the control code to a seperate file.
##
## For more information about these decorators and marsutils, see the docs at
## https://mars-utils.readthedocs.io/en/latest/
@with_ctrl_manager
## The main class in a magicbot robot must inherit `magicbot.MagicRobot`.
## A magicbot robot consists of the main class and then "components" which can access
## the variables defined in `createObjects()` and allows for sepration of code.
## https://robotpy.readthedocs.io/projects/utilities/en/latest/magicbot.html
class Kevin(magicbot.MagicRobot):
    # Magic components
    drive: Drive
    lift: Lift
    intake: Intake
    climb: Climb

    # Control modes
    primary: Primary

    # Controllers
    ## These controllers were intended to "take over" the human control in certain
    ## cases and drive the robot by sensors (camera vision and encoders) but were
    ## never finished or used
    ## cargo_align_ctrl: AlignCargo
    tape_align_ctrl: AlignTape

    # Dont add control chooser to smartdashboard
    ## This is a hack to move the control chooser widget on smartdashboard to
    ## the tab I wanted it on in shuffleboard (see `setup()``) for how it's moved
    ## (neither dashboard works very well..)
    _CONTROL_CHOOSER_DASHBOARD_KEY = None

    ## This is the first and one of the more important lifecycle functions.
    ## It is called when the robot turns on and is where every object that interacts with
    ## motors, encoders, gamepads, and other devices used by the robot is created
    ## and configured (note they must be instance variables, so they are defined on self).
    ##
    ## This function should not do any complex work as the robot will not function
    ## until this function finishes
    def createObjects(self):
        """Create magicbot components"""

        # Allow player control in sandstorm (2019 specific)
        self.use_teleop_in_autonomous = True

        # Inputs
        ## Gamepads for the primary and secondary driver in DS ports 0 and 1
        self.gamepad = wpilib.XboxController(0)
        self.gamepad2 = wpilib.XboxController(1)

        # Dashboard tabs
        ## These are the custom tabs I create to show on the DS dashboard
        ## Prefs contains things to be configured, Drive is what should be open
        ## when driving or in matches, and Debugging shows random info useful
        ## for fixing things
        self.prefs = Shuffleboard.getTab("Preferences")
        self.drive_tab = Shuffleboard.getTab("Drive")
        self.debug_tab = Shuffleboard.getTab("Debugging")

        # pi/jetson vision data
        ## This gets the NT entries that are updated by the pi or jetson
        ## computer vision code, the controllers access these fields to control
        ## the robot autonomously
        self.vision = NetworkTables.getTable("Vision")
        self.cargo_yaw = self.vision.getEntry("cargoYaw")
        self.tape_yaw = self.vision.getEntry("tapeYaw")
        self.cargo_detected = self.vision.getEntry("cargoDetected")
        self.tape_detected = self.vision.getEntry("tapeDetected")
        self.tape_mode = self.vision.getEntry("tape")

        # Drive motors
        ## One motor for each corner, indexed by CAN bus ID
        self.fl_drive = rev.CANSparkMax(2, rev.MotorType.kBrushless)
        self.fr_drive = rev.CANSparkMax(3, rev.MotorType.kBrushless)
        self.rl_drive = rev.CANSparkMax(4, rev.MotorType.kBrushless)
        self.rr_drive = rev.CANSparkMax(5, rev.MotorType.kBrushless)

        ## Drive encoders that tell us how far each wheel has spun using the
        ## spark max encoder api.  They are configured to use the neos hall effect
        ## sensors so that we don't need to mount optical encoders (and we don't need
        ## the precision of optical encoders)
        self.fl_drive_encoder = SparkMaxEncoder(self.fl_drive)
        self.fr_drive_encoder = SparkMaxEncoder(self.fr_drive)
        self.rl_drive_encoder = SparkMaxEncoder(self.rl_drive)
        self.rr_drive_encoder = SparkMaxEncoder(self.rr_drive)

        # Make the drive a little less jumpy
        ## Open loop refers to control via the .set(speed) functions (closed loop
        ## refers to the onboard PID control loops https://frc-pdr.readthedocs.io/en/latest/control/pid_control.html).
        ## These limit the neos to accelerate to full speed in .35 seconds, without
        ## them Kevin is near undrivable due to the speed of the drive train
        ## These most likely need to be changed on different robots or might not
        ## be neccessary
        self.fl_drive.setOpenLoopRampRate(0.35)
        self.fr_drive.setOpenLoopRampRate(0.35)
        self.rl_drive.setOpenLoopRampRate(0.35)
        self.rr_drive.setOpenLoopRampRate(0.35)

        # Wheel groups for tank mode
        ## Create a speed controller group for each side of the robot for tank mode
        ## where we want both motors on each side to spin at the same speed
        self.left_drive = wpilib.SpeedControllerGroup(self.fl_drive, self.rl_drive)
        self.right_drive = wpilib.SpeedControllerGroup(self.fr_drive, self.rr_drive)

        # Drive trains
        ## These classes in WPILib do the math to convert gamepad/joystick inputs
        ## to the proper motor speeds
        self.mecanum_drive = wpilib.drive.MecanumDrive(
            self.fl_drive, self.rl_drive, self.fr_drive, self.rr_drive
        )
        self.tank_drive = wpilib.drive.DifferentialDrive(
            self.left_drive, self.right_drive
        )
        ## Motors, motor controllers, and drive train controllers have safeties
        ## that turn off their motors f they aren't being controlled.
        ## But in this case, we have two drive trains, and they don't know the other
        ## is being controlled, so we need to turn of the safties and do it ourself
        ## (see `components.drive`)
        # They can't tell the other is in control, so we just turn off the software safety
        self.mecanum_drive.setSafetyEnabled(False)
        self.tank_drive.setSafetyEnabled(False)

        # Lift

        # Comp
        self.lift_motor = ctre.WPI_TalonSRX(9)
        self.lift_follower = ctre.WPI_TalonSRX(8)
        ## The lift gearbox has two motors that must move at the same speed, so
        ## we tell one to follow the other and then just control the first
        self.lift_follower.set(ctre.ControlMode.Follower, 9)

        ## The gear box was reversed on practice bot and comp bot, so this is here
        ## to keep the control code the same
        self.lift_motor.setInverted(True)
        self.lift_follower.setInverted(True)
        ## We use an optical encoder for lift PID so the lift can stay were we want
        ## it and we can use setpoints so the drivers dont have to worry about
        ## lining up.
        self.lift_encoder = ExternalEncoder(0, 1, reversed=False)

        # Intake
        self.wrist_motor = ctre.WPI_TalonSRX(10)
        self.wrist_motor.setInverted(True)
        self.intake_motor = ctre.WPI_TalonSRX(11)
        # I don't think this comment is relevant, but I don't remember why I wrote it
        # NOTE: Practice Bot (is this comment still relevant?)
        ## The wrist uses a CTRE absolute magnetic encoder (this means it always
        ## the same degree measurement accross robot restarts, optical encoders
        ## only measure the relative motion from the time the robot was turned on)
        self.wrist_encoder = AbsoluteMagneticEncoder(2)

        # Pneumatics

        # Intake grabber pistons
        self.intake_grabber_piston = wpilib.DoubleSolenoid(4, 5)

        ## We create a compressor object (default CAN ID of 0) so that we can turn
        ## it on or off from the gamepad (it's loud, annoying, and uses a lot of power)
        self.compressor = wpilib.Compressor()
        self.octacanum_shifter_front = wpilib.DoubleSolenoid(0, 1)
        self.octacanum_shifter_rear = wpilib.DoubleSolenoid(2, 3)
        ## This tries to make sure the octacanum starts in the right place,
        ## it shouldn't actually do anything but it makes me feel better, so it's
        ## still here
        # Default state is extended (mecanum)
        self.octacanum_shifter_front.set(wpilib.DoubleSolenoid.Value.kForward)
        self.octacanum_shifter_rear.set(wpilib.DoubleSolenoid.Value.kForward)

        # Climbing
        self.climb_piston = wpilib.DoubleSolenoid(6, 7)
        self.climb_piston.set(wpilib.DoubleSolenoid.Value.kForward)

        self.leg1 = rev.CANSparkMax(12, rev.MotorType.kBrushed)
        # self.leg2 = rev.CANSparkMax(13, rev.MotorType.kBrushed)
        # self.leg1 = ctre.WPI_TalonSRX(12)
        # self.leg2 = ctre.WPI_TalonSRX(13)

        # self.leg_drive = ctre.WPI_TalonSRX(17)
        self.leg_drive = rev.CANSparkMax(17, rev.MotorType.kBrushed)

        ## The navx is mounted on the rio (the center port is called the MXP)
        ## and we communicate with it over SPI through the MXP port.
        ## The navx is an AHRS (Attitude and heading reference system) which means
        ## it can tell us lots of information about where we are in the real world
        ##
        ## We just use it to get its (really nice) gyroscope for use in auto (how
        ## many degrees have we turned so far) and for FOD (Field-oriented drive)
        ## (how many degrees have we turned since the robot started)
        ##
        ## There are smaller and cheaper gyroscopes that can be mounted on the rio
        ## however they usually have pretty bad drive, which means over time they
        ## give an increasingly wrong reading.  The navx is better quality and
        ## fuses it's magnetometer (compass) readings to ensure its gyro angle stays
        ## accurate
        # Misc components
        self.navx = navx.AHRS.create_spi()

        ## This code is amazing for finding problems because it shows how much
        ## power each component is drawing on the dashboard (it can find stalled
        ## motors and more!).
        ## Unfortunately at the beginning of 2019 it was also responsible for
        ## causing the motors to set their speed to 0 every few seconds.
        ## (It should be fixed in future years)

        # PDP for monitoring power usage
        # WARN: Causes drive to stutter
        # self.pdp = wpilib.PowerDistributionPanel(0)
        # self.pdp.clearStickyFaults()
        # self.debug_tab.add(title="PDP", value=self.pdp)

        # WARN: Causes drive to stutter
        # self.debug_tab.add(self.mecanum_drive)
        # self.debug_tab.add(self.tank_drive)

        ## Add the encoders to the debugging tab for debugging
        encoders_list = self.debug_tab.getLayout("List", "Drive Encoders")
        encoders_list.add(title="Front Left", value=self.fl_drive_encoder)
        encoders_list.add(title="Front Right", value=self.fr_drive_encoder)
        encoders_list.add(title="Rear Left", value=self.rl_drive_encoder)
        encoders_list.add(title="Rear Right", value=self.rr_drive_encoder)
        self.debug_tab.add(title="Lift Encoder", value=self.lift_encoder)

        self.wrist_pos_dashboard = self.debug_tab.add(
            value=0, title="Wrist Pos"
        ).getEntry()

        ## Start a camera server from the rio and (hopefuly...) stream it to the dashboard
        # Launch camera server
        ## (I changed this and I guess I forgot to comment out this comment..)
        # Disabled: Vision sent through Jetson/Pi
        wpilib.CameraServer.launch()

        ## Blinking lights are great so this class manages the serial comunication
        ## with an arduino to control some addressable LED strips to display patterns
        ## when we perform certain actions.
        # Connect to ardunio controlled leds
        self.led_manager = LEDManager()

        ## Wait for the arduino to connect (in the background so we don' block the robot)
        ## and have it start the "alliance fader" pattern which displays our alliance
        ## color on the LEDs. Just in case somebody can't tell which alliance we are on....
        ##
        ## (only do it if we aren't in a simulation)
        if self.isReal():
            wpilib.Notifier(lambda: self.led_manager.alliance_fader()).startSingle(2)

    ## This is the special function that is called because of `@with_setup`
    def setup(self):
        ## Take the private reference to the control manager chooser and put it on the drive tab
        self.drive_tab.add(self._control_manager.control_chooser, title="Control_Mode")
        ## We then need to add a listener so that it knows when we change the value
        ## on the dashboard
        self._control_manager.setup_listener("Shuffleboard/Drive/Control_Mode")

    ## 2019 doesn't have a true auto period, so this function exists to forward
    ## control to teleop mode controls because the robot still is in auto modo.
    def autonomous(self):
        """Prepare for autonomous mode"""

        # This forwards input to teleopPerodic during the sandstorm
        magicbot.MagicRobot.autonomous(self)

    ## To make it easier to see who is holding the primary gamepad, we make it
    ## rumble when the robot is enabled
    # Make the primary controller rumble briefly
    def teleopInit(self):
        rumble.rumble(
            self.gamepad,
            duration=0.75,
            kind=wpilib.interfaces.GenericHID.RumbleType.kRightRumble,
        )

    ## Make sure the gamepad isn't rumbling and display the alliance fader
    def disabledInit(self):
        # Make sure the controller isnt stuck rumbling
        rumble.stop_rumble(
            self.gamepad, wpilib.interfaces.GenericHID.RumbleType.kRightRumble
        )
        self.led_manager.alliance_fader()


## Magic incantation to only run the robot code if the program has been run
## https://docs.python.org/3/library/__main__.html
if __name__ == "__main__":
    # Run robot
    wpilib.run(Kevin)
