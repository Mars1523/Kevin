import ctre


class Intake:
    intake_motor: ctre.WPI_TalonSRX
    wrist_motor: ctre.WPI_TalonSRX

    def __init__(self):
        self.speed = 0
        self.wrist_speed = 0

    def set_speed(self, speed):
        self.speed = speed

    def set_wrist(self, speed):
        self.wrist_speed = speed

    def execute(self):
        self.intake_motor.set(ctre.ControlMode.PercentOutput, self.speed)
        self.wrist_motor.set(ctre.ControlMode.PercentOutput, self.wrist_speed)
