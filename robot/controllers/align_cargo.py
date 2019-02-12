from networktables.entry import NetworkTableEntry

from components.drive import Drive, DriveMode


class AlignCargo:
    drive: Drive
    cargo_yaw: NetworkTableEntry

    def setup(self):
        self.enabled = False

    def set_enabled(self, enabled):
        self.enabled = enabled

    def execute(self):
        if self.enabled:
            yaw = self.cargo_yaw.getNumber(0)
            self.drive.set_mode(DriveMode.MECANUM)
            if yaw > 1:
                self.drive.drive_mecanum(0.24, 0.24, 0, adjusted=False)
                # pass
            elif yaw < -1:
                # pass
                self.drive.drive_mecanum(-0.24, 0.24, 0, adjusted=False)
            else:
                self.drive.drive_mecanum(0, 0, 0, adjusted=False)
