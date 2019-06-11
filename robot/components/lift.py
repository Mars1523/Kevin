from ctre.basemotorcontroller import BaseMotorController
import wpilib
from common.encoder import BaseEncoder


# Any setpoint is capped at this value
LIFT_ENCODER_MAX = 1980


class Lift:
    """
        A position PID enabled lift with preset heights
    """

    lift_motor: BaseMotorController
    lift_encoder: BaseEncoder

    def setup(self):
        self.speed = 0
        self.setpoint = 0
        self.pid_controller = wpilib.PIDController(
            0.00255, 0.0, 0.0, self.lift_encoder, self.lift_motor
        )
        self.pid_controller.setAbsoluteTolerance(0.5)
        self.pid_controller.setContinuous(False)
        self.pid_controller.setOutputRange(-0.5, 1.0)
        self.pid_controller.setSetpoint(0)
        self.pid_controller.enable()

    def set_speed(self, speed):
        self.speed = speed

    def set_setpoint(self, setpoint):
        self.setpoint = max(0, min(setpoint, LIFT_ENCODER_MAX))

    def get_setpoint(self):
        return self.pid_controller.getSetpoint()

    def execute(self):
        self.pid_controller.setSetpoint(self.setpoint)
