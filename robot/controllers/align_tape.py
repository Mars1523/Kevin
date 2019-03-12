import wpilib
import wpilib.interfaces

from networktables.entry import NetworkTableEntry
from wpilib.shuffleboard import ShuffleboardTab

from components.drive import Drive, DriveMode

#
# class PID(wpilib.interfaces.PIDSource, wpilib.interfaces.PIDOutput):
#     output = 0.0
#
#     def __init__(self, yaw):
#         self.yaw = yaw
#
#     def getPIDSourceType(self) -> wpilib.interfaces.PIDSource.PIDSourceType:
#         return wpilib.interfaces.PIDSource.PIDSourceType.kDisplacement
#
#     def pidGet(self) -> float:
#         return self.yaw.getNumber(0.0)
#
#     def pidWrite(self, output: float) -> None:
#         self.output = output


class AlignTape:
    drive: Drive
    tape_yaw: NetworkTableEntry
    tape_detected: NetworkTableEntry
    debug_tab: ShuffleboardTab

    def setup(self):
        self.enabled = False
        # self.pid_source = PID(self.cargo_yaw)
        self.pid = wpilib.PIDController(
            # 0.045, 0.0002, 0.04, 0, self.pid_source, self.pid_source
            0.078,
            0.005,
            0.04,
            0,
            self.get_yaw,
            self.set_output,
        )
        self.pid.setAbsoluteTolerance(5)
        self.pid.setContinuous(False)
        self.pid.setOutputRange(-0.7, 0.7)
        # self.pid.enable()
        self.pid.setSetpoint(-4)
        self.output = 0
        self.on_target = False

        self.debug_tab.add(title="Auto Driving Tape PID", value=self.pid)

    def set_enabled(self, enabled):
        self.enabled = enabled
        # if enabled:
        #     self.on_target = False

    def get_yaw(self):
        return self.tape_yaw.getNumber(0.0)

    def set_output(self, output):
        self.output = output

    def execute(self):
        # forward = 0.55 if self.on_target else 0
        self.pid.setEnabled(self.enabled and self.tape_detected.getBoolean(False))
        if self.enabled:
            self.drive.set_mode(DriveMode.MECANUM)
            # self.drive.drive_mecanum(-self.pid_source.output, forward, 0)
            # yaw = abs(self.pid_source.yaw.getNumber(0))
            self.drive.drive_mecanum(-self.output, 0, 0)
            # yaw = abs(self.e.yaw.getNumber(0))
            # print(self.pid_source.output, self.on_target, yaw)
            self.on_target = self.tape_detected.getBoolean(False)
            print("charge" if self.on_target else "seek")
