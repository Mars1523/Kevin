import ctre
import wpilib
from common.srx_mag_encoder import AbsoluteMagneticEncoder
import networktables.entry


class Intake:
    intake_motor: ctre.WPI_TalonSRX
    wrist_motor: ctre.WPI_TalonSRX
    intake_piston: wpilib.DoubleSolenoid
    wrist_encoder: AbsoluteMagneticEncoder
    wrist_pos_dashboard: networktables.entry.NetworkTableEntry

    def setup(self):
        self.speed = 0
        self.wrist_setpoint = 0
        self.extend = False

        self.pid_controller = wpilib.PIDController(
            0.02555, 0.0, 0.0, self.wrist_encoder, self.wrist_motor
        )
        self.pid_controller.setAbsoluteTolerance(0.5)
        self.pid_controller.setContinuous(False)
        self.pid_controller.setOutputRange(-0.65, 0.65)
        self.pid_controller.setSetpoint(120)
        self.pid_controller.enable()

    def set_speed(self, speed):
        self.speed = speed

    def set_wrist_setpoint(self, setpoint):
        clamped = max(120, min(197, setpoint))
        self.wrist_setpoint = clamped

    def set_wrist(self, speed):
        self.wrist_setpoint = speed

    def extend_piston(self):
        self.extend = True

    def retract_piston(self):
        self.extend = False

    def execute(self):
        self.wrist_pos_dashboard.setNumber(self.wrist_encoder.get_angle())
        self.intake_motor.set(ctre.ControlMode.PercentOutput, self.speed)

        self.pid_controller.setSetpoint(self.wrist_setpoint)

        self.intake_piston.set(
            wpilib.DoubleSolenoid.Value.kForward
            if self.extend
            else wpilib.DoubleSolenoid.Value.kReverse
        )
