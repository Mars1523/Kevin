import wpilib
from wpilib.interfaces import PIDSource

# TODO: Is this ~~trip~~ really necessary and if so, merge it into marsutils


class BaseEncoder(wpilib.interfaces.PIDSource):
    """
        This class deals with the zeroing and reading
        encoders
    """

    def get(self) -> int:
        return 0.0

    def zero(self):
        pass

    def getPIDSourceType(self) -> PIDSource.PIDSourceType:
        return PIDSource.PIDSourceType.kDisplacement

    def pidGet(self) -> int:
        return self.get()


class CANTalonEncoder(BaseEncoder):
    """
        This class deals with the zeroing and reading
        from the encoders connected to motor controllers
    """

    def __init__(self, motor, is_reversed=False):
        self.motor = motor
        if is_reversed:
            self.mod = -1
        else:
            self.mod = 1
        self.initialValue = self.mod * self.motor.getAnalogInPosition()

    def get(self) -> int:
        return (self.mod * self.motor.getAnalogInPosition()) - self.initialValue

    def zero(self):
        self.initialValue = self.mod * self.motor.getAnalogInPosition()


class ExternalEncoder(BaseEncoder):
    """
        This class deals with the zeroing and reading
        from the encoders connected over DIO
    """

    def __init__(
        self,
        chan_a,
        chan_b,
        is_reversed=False,
        encoding_type=wpilib.Encoder.EncodingType.k4X,
    ):
        self.encoder = wpilib.Encoder(chan_a, chan_b, is_reversed, encoding_type)
        self.initialValue = self.encoder.getDistance()

    def get(self) -> int:
        return self.encoder.getDistance()

    def zero(self):
        self.encoder.reset()
