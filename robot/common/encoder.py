import wpilib
from wpilib.interfaces import PIDSource

import rev
import ctre

# TODO: Merge into marsutils


class BaseEncoder(wpilib.interfaces.PIDSource, wpilib.sendablebase.SendableBase):
    """
        BaseEncoder provides a consistent interface to encoders
    """

    def get_position(self) -> float:
        """
        Gets position from the feedback sensor
        :return: current position
        """
        raise NotImplementedError

    def get_velocity(self) -> float:
        """
        Gets velocity from the feedback sensor
        :return: current velocity
        """
        raise NotImplementedError

    def zero(self):
        """
        Resets the current position to zero
        """
        raise NotImplementedError

    def setPIDSourceType(self, pidSource: PIDSource.PIDSourceType) -> None:
        raise NotImplementedError

    def getPIDSourceType(self) -> PIDSource.PIDSourceType:
        return PIDSource.PIDSourceType.kDisplacement

    def pidGet(self) -> float:
        """
        Input for PIDSource
        :return: feedback position
        """
        return self.get_position()

    def initSendable(self, builder: wpilib.SendableBuilder) -> None:
        builder.setSmartDashboardType("Encoder")

        builder.addDoubleProperty("Speed", self.get_velocity, None)
        builder.addDoubleProperty("Distance", self.get_position, None)


class CANTalonEncoder(BaseEncoder):
    """
        This class deals with the zeroing and reading
        from the encoders connected to motor controllers
    """

    def __init__(self, motor, reversed=False):
        self.motor = motor
        if reversed:
            self.mod = 1
        else:
            self.mod = -1
        self.initialValue = self.mod * self.motor.getQuadraturePosition()

    def get_position(self) -> int:
        return (self.mod * self.motor.getQuadraturePosition()) - self.initialValue

    def zero(self):
        self.initialValue = self.mod * self.motor.getQuadraturePosition()


class CANTalonQuadEncoder(BaseEncoder):
    """
        Access quadrature encoders connected to CTRE Talons
    """

    def __init__(self, motor: ctre.WPI_TalonSRX, reversed=False):
        self.motor = motor
        if reversed:
            self.mod = -1
        else:
            self.mod = 1

    def zero(self):
        self.motor.setQuadraturePosition(0)

    def get_position(self) -> float:
        return self.mod * self.motor.getQuadraturePosition()

    def get_velocity(self) -> float:
        return self.motor.getQuadratureVelocity()


class CANTalonAnalogEncoder(BaseEncoder):
    """
        Access analog encoders connected to CTRE Talons
    """

    def __init__(self, motor: ctre.WPI_TalonSRX, reversed=False):
        self.motor = motor
        if reversed:
            self.mod = -1
        else:
            self.mod = 1

    def zero(self):
        self.motor.setAnalogPosition(0)

    def get_position(self) -> float:
        return self.mod * self.motor.getAnalogIn()

    def get_velocity(self) -> float:
        return self.motor.getAnalogInVel()


class SparkMaxEncoder(BaseEncoder):
    """
        Access Spark Max hall sensors or external sensors
    """

    def __init__(self, motor: rev.CANSparkMax, reversed=False):
        self.encoder = motor.getEncoder()
        if reversed:
            self.mod = -1
        else:
            self.mod = 1
        self.initialValue = self.mod * self.encoder.getPosition()

    def zero(self):
        self.initialValue = self.mod * self.encoder.getPosition()

    def get_position(self) -> float:
        return (self.mod * self.encoder.getPosition()) - self.initialValue

    def get_velocity(self) -> float:
        return self.encoder.getVelocity()


class ExternalEncoder(BaseEncoder):
    """
        This class provides access to encoders connected over DIO
    """

    def __init__(
        self,
        chan_a,
        chan_b,
        reversed=False,
        encoding_type=wpilib.Encoder.EncodingType.k4X,
    ):
        self.encoder = wpilib.Encoder(chan_a, chan_b, reversed, encoding_type)
        self.initialValue = self.encoder.getDistance()

    def get_position(self) -> float:
        return self.encoder.getDistance()

    def get_velocity(self) -> float:
        return self.encoder.getRate()

    def zero(self):
        self.encoder.reset()
