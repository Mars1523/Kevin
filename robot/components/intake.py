import ctre
import wpilib
from common.srx_mag_encoder import AbsoluteMagneticEncoder
import networktables.entry
from components import Lift


class Intake:
    """
        The intake uses `intake_motor` to spin wheels to pick up balls,
        `wrist_motor` to move the intake and uses an srx abs magnetic encoder
        wired to the rio for PID

        The intake uses `intake_grabber_piston` to move two forks outward
        to grab the hatch
    """

    intake_motor: ctre.WPI_TalonSRX
    wrist_motor: ctre.WPI_TalonSRX
    # Front intake
    intake_grabber_piston: wpilib.DoubleSolenoid
    # Rear intake
    # intake_piston: wpilib.DoubleSolenoid
    wrist_encoder: AbsoluteMagneticEncoder
    wrist_pos_dashboard: networktables.entry.NetworkTableEntry

    def setup(self):
        self.speed = 0
        self.wrist_setpoint = 273
        self.extend = False
        self.grab = False

        self.pid_controller = wpilib.PIDController(
            0.0256, 0.0, 0.0, self.wrist_encoder, self.wrist_motor
        )
        self.pid_controller.setAbsoluteTolerance(0.5)
        self.pid_controller.setContinuous(False)
        self.pid_controller.setOutputRange(-1, 1)
        self.pid_controller.setSetpoint(self.wrist_setpoint)
        # 136-215-220 (changed) 281-208-270
        self.pid_controller.enable()

    def set_speed(self, speed):
        self.speed = speed

    def set_wrist_setpoint(self, setpoint):
        clamped = max(208, min(273, setpoint))
        self.wrist_setpoint = clamped

    def set_wrist(self, speed):
        self.wrist_setpoint = speed

    # Pull the intake in tightly to avoid frame perimeter calls
    def set_defense(self):
        self.wrist_setpoint = 280

    def extend_piston(self):
        self.extend = True

    def retract_piston(self):
        self.extend = False

    def grab_hatch(self):
        self.grab = True

    def release_hatch(self):
        self.grab = False

    def toggle_grab(self):
        self.grab = not self.grab

    def execute(self):
        # self.wrist_pos_dashboard.setNumber(self.wrist_encoder.get_angle())
        self.wrist_pos_dashboard.setNumber(self.wrist_setpoint)
        self.intake_motor.set(ctre.ControlMode.PercentOutput, self.speed)

        self.pid_controller.setSetpoint(self.wrist_setpoint)

        self.intake_grabber_piston.set(
            wpilib.DoubleSolenoid.Value.kForward
            if self.grab
            else wpilib.DoubleSolenoid.Value.kReverse
        )
