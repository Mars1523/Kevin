import ctre


class Lift:
    """
        A position PID enabled lift with preset heights
    """

    lift_motor: ctre.WPI_VictorSPX

    def __init__(self):
        self.speed = 0

    def set_speed(self, speed):
        self.speed = speed

    def execute(self):
        # feed the other drive train to appease the motor safety
        self.lift_motor.set(ctre.ControlMode.PercentOutput, self.speed)
