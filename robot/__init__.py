import magicbot
import wpilib
from marsutils import with_ctrl_manager

from .components import Drive
from .controls import Testing


@with_ctrl_manager
class Kevin(magicbot.MagicRobot):
    # Magic components
    drive: Drive

    # Control modes
    testing: Testing

    def createObjects(self):
        """Create magicbot components"""
        # Inputs
        self.gamepad = wpilib.XboxController(0)

        # Drive motors
        # TODO: Change these to CAN
        self.fl_drive = wpilib.Spark(0)
        self.fr_drive = wpilib.Spark(1)
        self.rl_drive = wpilib.Spark(2)
        self.rr_drive = wpilib.Spark(3)

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

        # Misc components

        # PDP for monitoring power usage
        self.pdp = wpilib.PowerDistributionPanel(0)
        wpilib.SmartDashboard.putData("PowerDistributionPanel", self.pdp)

        # Launch camera server
        wpilib.CameraServer.launch()

    def autonomous(self):
        """Prepare for autonomous mode"""

        magicbot.MagicRobot.autonomous(self)
