## This file contains the code responsible for driving the simulatio physics.
## Every "tick" the `update_sim()` function is called, and the `hal_data` parameter
## contains the complete state of the robot components, such as motor controllers, encoders,
## and solenoids.
## By reading that data, we can tell the `physics_controller` what those inputs mean.  For instance, we
## feed a drive train simulator our motor inputs and it will compute how far the robot has moved,
## we then feed that to the physics controller which updates our robot in the simulator.
## We can also do things like update encoder values and gyro readings.
##
## Documentation can be found by robotpy here
## https://robotpy.readthedocs.io/projects/pyfrc/en/stable/physics.html
## and some information has been documented by me here
## https://mars1523.github.io/nomicon/simulation/getting_started.html
##
## Implementing this can be fairly tricky, and documentation (as of 2019) is fairly sparse,
## with that said, it can be very helpful to look at the robotpy physics samples on github
## https://github.com/robotpy/examples as well as searching around for other teams robots code.
## If that fails, A listing of all the `hal_data` values can be found in the robotpy code
## https://github.com/robotpy/robotpy-wpilib/blob/master/hal-sim/hal_impl/data.py
##
## The code in this file is (currently) far from perfect example, but it could provide
## some insight for future robots.
## As it is currently implemented, it is not an _accurate_, but it works well
## enough for me to know a change I made didn't break the robot.

from pyfrc.physics import drivetrains, motion
import math

## Here we define some constants for calculating encoder distance.
## `ENCODER_REVOLUTION` is the number of "ticks" in an optical encoder, or more
## generally, the value reported by the encoder after it has made a full revolution.
## (in this case I think it should be 4096, the default for E4P encoders)
ENCODER_REVOLUTION = 1024

## (TODO: Figure out why I wrote this and what it is supposed to be)
ENCODER_TICKS = ENCODER_REVOLUTION / (0.5 * math.pi)


## The PhysicsEngine class is initalized automatically by the simulator, you don't
## need to start it like the main robot class.
class PhysicsEngine:
    def __init__(self, physics_controller):
        """
        :param physics_controller: `pyfrc.physics.core.Physics` object
                                   to communicate simulation effects to
        """

        ## Here we want to define the state for representing our robot in the real
        ## world, things like encoders.
        self.fl_encoder = self.fr_encoder = self.rl_encoder = self.rr_encoder = 0
        self.wrist_encoder = 0
        self.physics_controller = physics_controller

        """
        # Change these parameters to fit your robot!
        """

        ## Here we define some helpers that do most of the math for us.
        ## The lift can be simulated by using a `LinearMotion` helper, although
        ## the values here are not accurate for the robot.
        # Create a lift simulation
        self.lift_motion = motion.LinearMotion("Lift", 6, 360)

        ## Here we define the two drive train helpers.  Most robots will likely
        ## be tank drive and use the `TankModel` simulator, and implements a
        ## more vaguely realistic simulation than most of the other drive train
        ## simulations.
        self.mecaum_drivetrain = drivetrains.MecanumDrivetrain(
            x_wheelbase=2, y_wheelbase=2, speed=5
        )

        self.tank_drivetrain = drivetrains.FourMotorDrivetrain(x_wheelbase=2, speed=5)

        ## Simulate the gyroscope on the navx.
        ##
        ## This magical string was found in the code here:
        ## https://github.com/robotpy/robotpy-navx/blob/5e68a730d1542e8ab18132ff7d06cb35ec3b7612/navx/_impl/sim_io.py
        self.physics_controller.add_device_gyro_channel("navxmxp_spi_4_angle")

    def update_sim(self, hal_data, now, tm_diff):
        """
        Called when the simulation parameters for the program need to be
        updated.

        :param now: The current time as a float
        :param tm_diff: The amount of time that has passed since the last
                        time that this function was called
        """

        is_tank = not hal_data["solenoid"][1]["value"]

        # Simulate the drivetrain
        # right motors must be inverted
        front_l = hal_data["CAN"]["sparkmax-2"]["value"]
        front_r = -hal_data["CAN"]["sparkmax-3"]["value"]
        rear_l = hal_data["CAN"]["sparkmax-4"]["value"]
        rear_r = -hal_data["CAN"]["sparkmax-5"]["value"]

        # TODO: The encoder math is _completely_ wrong
        if is_tank:
            speed, rotation = self.tank_drivetrain.get_vector(
                rear_l, rear_r, front_l, front_r
            )
            self.physics_controller.drive(speed, rotation, tm_diff)
            self.fl_encoder += self.tank_drivetrain.l_speed * tm_diff * 10
            self.fr_encoder += self.tank_drivetrain.r_speed * tm_diff * 10
            self.rl_encoder += self.tank_drivetrain.l_speed * tm_diff * 10
            self.rr_encoder += self.tank_drivetrain.r_speed * tm_diff * 10

        else:
            x_speed, y_speed, rotation = self.mecaum_drivetrain.get_vector(
                rear_l, rear_r, front_l, front_r
            )
            self.physics_controller.vector_drive(x_speed, y_speed, rotation, tm_diff)
            self.fl_encoder += self.mecaum_drivetrain.lf_speed * tm_diff * 1000
            self.fr_encoder += self.mecaum_drivetrain.rf_speed * tm_diff * 1000
            self.rl_encoder += self.mecaum_drivetrain.lr_speed * tm_diff * 1000
            self.rr_encoder += self.mecaum_drivetrain.rr_speed * tm_diff * 1000
        hal_data["CAN"]["sparkmax-2"]["quad_position"] = int(
            self.fl_encoder * ENCODER_TICKS
        )
        hal_data["CAN"]["sparkmax-4"]["quad_position"] = int(
            self.fr_encoder * ENCODER_TICKS
        )
        hal_data["CAN"]["sparkmax-3"]["quad_position"] = int(
            self.rl_encoder * ENCODER_TICKS
        )
        hal_data["CAN"]["sparkmax-5"]["quad_position"] = int(
            self.rr_encoder * ENCODER_TICKS
        )

        # Simulate the lift encoders
        hal_data["encoder"][0]["count"] = self.lift_motion.compute(
            hal_data["CAN"][8]["value"], tm_diff
        )

        # Simulate the wrist encoders
        self.wrist_encoder += hal_data["CAN"][10]["value"] * tm_diff * 1000
        hal_data["encoder"][1]["count"] = self.wrist_encoder
        hal_data["encoder"][1]["distance_per_pulse"] = 1
