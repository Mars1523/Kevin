import ctre
import wpilib


class Intake:
    intake_motor: ctre.WPI_TalonSRX
    wrist_motor: ctre.WPI_TalonSRX
    intake_piston: wpilib.DoubleSolenoid

    def __init__(self):
        self.speed = 0
        self.wrist_speed = 0

        self.extend = False

    def set_speed(self, speed):
        self.speed = speed

    def set_wrist(self, speed):
        self.wrist_speed = speed

    def extend_piston(self):
        self.extend = True

    def retract_piston(self):
        self.extend = False

    def execute(self):
        self.intake_motor.set(ctre.ControlMode.PercentOutput, self.speed)
        self.wrist_motor.set(ctre.ControlMode.PercentOutput, self.wrist_speed)

        self.intake_piston.set(
            wpilib.DoubleSolenoid.Value.kForward
            if self.extend
            else wpilib.DoubleSolenoid.Value.kReverse
        )
