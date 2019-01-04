import magicbot
import wpilib


class Mars2019(magicbot.MagicRobot):
    # Magic components
    ...

    # Control modes
    ...

    def createObjects(self):
        """Create magicbot components"""
        # Inputs
        ...

        # Drive motors
        ...

        # Drive train
        ...

        # Misc components

        # PDP for monitoring power usage
        self.pdp = wpilib.PowerDistributionPanel(0)
        wpilib.SmartDashboard.putData("PowerDistributionPanel", self.pdp)

        # Launch camera server
        wpilib.CameraServer.launch()

    def autonomous(self):
        """Prepare for autonomous mode"""

        magicbot.MagicRobot.autonomous(self)


if __name__ == "__main__":
    # Run robot
    wpilib.run(Mars2019)
