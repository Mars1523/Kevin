import wpilib
import wpilib.interfaces
from wpilib.interfaces import PIDSource
import time


# TODO: Move to marsutils
class AbsoluteMagneticEncoder(wpilib.interfaces.PIDSource):
    def __init__(self, pwm_channel):
        self.counter = wpilib.Counter(pwm_channel)
        self.counter.setSemiPeriodMode(True)  # only count rising edges

        time.sleep(0.5)

        self.offsetDegrees = self.get_angle()

    def clear(self):
        self.offsetDegrees = 0

    def get_angle(self):
        return ((self.counter.getPeriod() - 1e-6) / 4095e-6) * 360  # returns degrees

    def get_raw(self):
        return self.counter.getPeriod()

    def getPIDSourceType(self) -> PIDSource.PIDSourceType:
        return PIDSource.PIDSourceType.kDisplacement

    def pidGet(self):
        return self.get_angle()
