import magicbot
import wpilib
import wpilib.drive
from wpilib.shuffleboard import Shuffleboard
import rev
import ctre
import navx
from marsutils import with_ctrl_manager, with_setup

from components import Drive, Lift
from controls import Primary


# Order matters
@with_setup
@with_ctrl_manager
class Kevin(magicbot.MagicRobot):
    # Magic components
    drive: Drive
    lift: Lift

    # Control modes
    primary: Primary

    # Dont add control chooser to smartdashboard
    _CONTROL_CHOOSER_DASHBOARD_KEY = None

    def createObjects(self):
        """Create magicbot components"""

        # Inputs
        self.gamepad = wpilib.XboxController(0)
        self.gamepad2 = wpilib.XboxController(1)

        # Dashboard items
        self.prefs = Shuffleboard.getTab("Preferences")
        self.drive_tab = Shuffleboard.getTab("Drive")
        self.debug_tab = Shuffleboard.getTab("Debugging")

        self.curiosity_compat = (
            self.prefs.addPersistent("curiosity_compat", False)
            .withWidget("Toggle Box")
            .getEntry()
        )

        # Drive motors
        # Curisoity has talons, we can use it for testing
        if self.curiosity_compat.get():
            self.fl_drive = ctre.WPI_TalonSRX(10)
            self.fr_drive = ctre.WPI_TalonSRX(11)
            self.rl_drive = ctre.WPI_TalonSRX(12)
            self.rr_drive = ctre.WPI_TalonSRX(13)
        # TODO: Spark max does not have sim support yet, use talons instead for now
        elif self.isSimulation():
            self.fl_drive = ctre.WPI_TalonSRX(2)
            self.fr_drive = ctre.WPI_TalonSRX(3)
            self.rl_drive = ctre.WPI_TalonSRX(4)
            self.rr_drive = ctre.WPI_TalonSRX(5)
        else:
            self.fl_drive = rev.CANSparkMax(2, rev.MotorType.kBrushless)
            self.fr_drive = rev.CANSparkMax(3, rev.MotorType.kBrushless)
            self.rl_drive = rev.CANSparkMax(4, rev.MotorType.kBrushless)
            self.rr_drive = rev.CANSparkMax(5, rev.MotorType.kBrushless)

        # left
        self.left_drive = wpilib.SpeedControllerGroup(self.fl_drive, self.rl_drive)
        # right
        self.right_drive = wpilib.SpeedControllerGroup(self.fr_drive, self.rr_drive)

        # Drive trains
        self.mecanum_drive = wpilib.drive.MecanumDrive(
            self.fl_drive, self.rl_drive, self.fr_drive, self.rr_drive
        )
        self.mecanum_drive.setDeadband(0.06)
        self.tank_drive = wpilib.drive.DifferentialDrive(
            self.left_drive, self.right_drive
        )

        # Lift
        self.lift_motor = ctre.WPI_VictorSPX(8)
        self.lift_follower = ctre.WPI_VictorSPX(9)
        self.lift_follower.set(ctre.ControlMode.Follower, 8)

        # Pneumatics
        self.octacanum_shifter = wpilib.DoubleSolenoid(0, 1)
        # Default state is extended (mecanum)
        self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kForward)
        # Misc components

        self.navx = navx.AHRS.create_spi()

        # PDP for monitoring power usage
        self.pdp = wpilib.PowerDistributionPanel(1)
        self.debug_tab.add(title="PDP", value=self.pdp)

        self.debug_tab.add(self.mecanum_drive)
        self.debug_tab.add(self.tank_drive)

        # Launch camera server
        wpilib.CameraServer.launch()

    def setup(self):
        self.drive_tab.add(self._control_manager.control_chooser, title="Control_Mode")
        self.drive_tab.add(4, title="Control_Mode2")
        self._control_manager.setup_listener("Shuffleboard/Drive/Control_Mode")

    def autonomous(self):
        """Prepare for autonomous mode"""

        magicbot.MagicRobot.autonomous(self)


if __name__ == "__main__":
    # Run robot
    wpilib.run(Kevin)
