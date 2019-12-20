import rev
import wpilib
from magicbot import will_reset_to


class Climb:
    # leg1: ctre.WPI_TalonSRX
    # leg2: ctre.WPI_TalonSRX

    leg1: rev.CANSparkMax
    # leg2: rev.CANSparkMax

    leg_drive: rev.CANSparkMax
    # leg_drive: ctre.WPI_TalonSRX

    climb_piston: wpilib.DoubleSolenoid

    def setup(self):
        self.extend = will_reset_to(False)
        self.knee_speed = will_reset_to(0)
        self.drive_speed = will_reset_to(0)

    def set_knee_speed(self, speed):
        self.knee_speed = speed

    def set_drive_speed(self, speed):
        self.drive_speed = speed

    def extend_piston(self):
        self.extend = True

    def retract_piston(self):
        self.extend = False

    def execute(self):
        self.leg1.set(self.knee_speed)
        # self.leg2.set(self.knee_speed)

        self.leg_drive.set(self.drive_speed)

        self.climb_piston.set(
            wpilib.DoubleSolenoid.Value.kReverse
            if self.extend
            else wpilib.DoubleSolenoid.Value.kForward
        )
