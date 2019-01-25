import magicbot
import wpilib
import wpilib.drive
from wpilib.shuffleboard import Shuffleboard
import rev
import ctre
from marsutils import with_ctrl_manager

from components import Drive
from controls import Test1, Test2


@with_ctrl_manager
class Kevin(magicbot.MagicRobot):
    # Magic components
    drive: Drive

    # Control modes
    test1: Test1
    test2: Test2

    def createObjects(self):
        """Create magicbot components"""

        # Inputs
        self.gamepad = wpilib.XboxController(0)

        # Dashboard items
        self.prefs = Shuffleboard.getTab("Preferences")

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
            # Additional motors
            self.fl_drive2 = ctre.WPI_TalonSRX(10)
            self.fr_drive2 = ctre.WPI_TalonSRX(11)
            self.rl_drive2 = ctre.WPI_TalonSRX(12)
            self.rr_drive2 = ctre.WPI_TalonSRX(13)
            self.fl_drive2.set(ctre.ControlMode.Follower, 2)
            self.fr_drive2.set(ctre.ControlMode.Follower, 3)
            self.rl_drive2.set(ctre.ControlMode.Follower, 4)
            self.rr_drive2.set(ctre.ControlMode.Follower, 5)
        else:
            self.fl_drive = rev.CANSparkMax(2, rev.MotorType.kBrushless)
            self.fr_drive = rev.CANSparkMax(3, rev.MotorType.kBrushless)
            self.rl_drive = rev.CANSparkMax(4, rev.MotorType.kBrushless)
            self.rr_drive = rev.CANSparkMax(5, rev.MotorType.kBrushless)
            # Additional motors
            self.fl_drive2 = rev.CANSparkMax(10, rev.MotorType.kBrushless)
            self.fr_drive2 = rev.CANSparkMax(11, rev.MotorType.kBrushless)
            self.rl_drive2 = rev.CANSparkMax(12, rev.MotorType.kBrushless)
            self.rr_drive2 = rev.CANSparkMax(13, rev.MotorType.kBrushless)
            # Follower api does not exist yet
            self.fl_drive = wpilib.SpeedControllerGroup(self.fl_drive, self.fl_drive2)
            self.fr_drive = wpilib.SpeedControllerGroup(self.fr_drive, self.fr_drive2)
            self.rl_drive = wpilib.SpeedControllerGroup(self.rl_drive, self.rl_drive2)
            self.rr_drive = wpilib.SpeedControllerGroup(self.rr_drive, self.rr_drive2)

        # left
        self.left_drive = wpilib.SpeedControllerGroup(self.fl_drive, self.rl_drive)
        # right
        self.right_drive = wpilib.SpeedControllerGroup(self.fr_drive, self.rr_drive)

        # Drive trains
        self.mecanum_drive = wpilib.drive.MecanumDrive(
            self.fl_drive, self.rl_drive, self.fr_drive, self.rr_drive
        )
        self.tank_drive = wpilib.drive.DifferentialDrive(
            self.left_drive, self.right_drive
        )

        # Pneumatics
        self.octacanum_shifter = wpilib.DoubleSolenoid(0, 1)
        # Default state is extended (mecanum)
        self.octacanum_shifter.set(wpilib.DoubleSolenoid.Value.kForward)
        # Misc components

        # PDP for monitoring power usage
        self.pdp = wpilib.PowerDistributionPanel(1)
        wpilib.SmartDashboard.putData("PowerDistributionPanel", self.pdp)

        # Launch camera server
        wpilib.CameraServer.launch()

    def autonomous(self):
        """Prepare for autonomous mode"""

        magicbot.MagicRobot.autonomous(self)


if __name__ == "__main__":
    # Run robot
    wpilib.run(Kevin)
