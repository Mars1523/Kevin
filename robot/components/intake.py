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

        ## This is a PID controller (which is a kind of closed loop control)
        ## which takes input from the wrist encoder, and uses that to control the
        ## wrist motor and hold it at a certain rotation.
        ##
        ## https://frc-pdr.readthedocs.io/en/latest/control/using_WPILIB's_pid_controller.html
        ##
        ## Interestingly, this is technically refered to a "P Loop", because
        ## there is only a "proportion" value, no I or D.
        self.pid_controller = wpilib.PIDController(
            0.0256, 0.0, 0.0, self.wrist_encoder, self.wrist_motor
        )
        ## Set the tolerance (this is only actually useful if you use the .onTarget()
        ## functions).  However, PID can be an arcane magic, and this code works.
        self.pid_controller.setAbsoluteTolerance(0.5)
        ## We do not want to the wrist to go backwards into the robot, so
        ## we tell the controller it is not a continuous circle.
        self.pid_controller.setContinuous(False)
        ## The motors accept speeds in a range of -1.0 to 1.0, so we tell the
        ## controller that is the range of values we want
        self.pid_controller.setOutputRange(-1, 1)
        ## Set the pid controller starting position so the pid controller does
        ## not try to send the wrist to zero degrees
        self.pid_controller.setSetpoint(self.wrist_setpoint)
        # 136-215-220 (changed) 281-208-270
        ## Actually turn on the controller.  Unless you call this, they won't do
        ## anything.  I have lost too much of my life to disabled PID controllers.
        self.pid_controller.enable()

    def set_speed(self, speed):
        self.speed = speed

    def set_wrist_setpoint(self, setpoint):
        ## This max(x, min(y, z)) thing ensures that the setpoint value never
        ## exeeds a minimum or maximum value, because that causes things to break.
        ##
        ## Note that the order of constant values here is _very_ important and
        ## the incorrect order will cause strange behavior.
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
