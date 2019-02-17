import wpilib
import wpilib.interfaces

from networktables.entry import NetworkTableEntry

from components.drive import Drive, DriveMode


class PID(wpilib.interfaces.PIDSource, wpilib.interfaces.PIDOutput):
    output = 0.0

    def __init__(self, yaw):
        self.yaw = yaw

    def getPIDSourceType(self) -> wpilib.interfaces.PIDSource.PIDSourceType:
        return wpilib.interfaces.PIDSource.PIDSourceType.kDisplacement

    def pidGet(self) -> float:
        return self.yaw.getNumber(0.0)

    def pidWrite(self, output: float) -> None:
        self.output = output


class AlignCargo:
    drive: Drive
    cargo_yaw: NetworkTableEntry

    def setup(self):
        self.enabled = False
        self.pid_source = PID(self.cargo_yaw)
        self.pid = wpilib.PIDController(
            0.045, 0.0002, 0.04, 0, self.pid_source, self.pid_source
        )
        self.pid.setAbsoluteTolerance(5)
        self.pid.setContinuous(False)
        self.pid.setOutputRange(-0.7, 0.7)
        self.pid.enable()
        self.output = 0
        self.on_target = False

    def set_enabled(self, enabled):
        self.enabled = enabled
        # if enabled:
        #     self.on_target = False

    def execute(self):
        forward = 0.55 if self.on_target else 0
        self.pid.setEnabled(self.enabled)
        self.drive.set_mode(DriveMode.MECANUM)
        self.drive.drive_mecanum(-self.pid_source.output, forward, 0)
        yaw = abs(self.pid_source.yaw.getNumber(0))
        # print(self.pid_source.output, self.on_target, yaw)
        self.on_target = yaw < 4
        print("seek", self.on_target)
