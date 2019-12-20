import wpilib.interfaces
from wpilib.interfaces import GenericHID


def rumble(gamepad: GenericHID, duration=0.25, kind=GenericHID.RumbleType.kLeftRumble):
    gamepad.setRumble(kind, 1)

    def stop():
        gamepad.setRumble(kind, 0)

    if wpilib.robotbase.RobotBase.isReal():
        wpilib.Notifier(stop).startSingle(duration)


def stop_rumble(gamepad: GenericHID, kind: GenericHID.RumbleType = None):
    if kind is None:
        gamepad.setRumble(GenericHID.RumbleType.kLeftRumble, 0)
        gamepad.setRumble(GenericHID.RumbleType.kRightRumble, 0)
    else:
        gamepad.setRumble(kind, 0)
