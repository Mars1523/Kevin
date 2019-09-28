from pyfrc.physics import drivetrains, motion
import math

ENCODER_REVOLUTION = 1024

ENCODER_TICKS = ENCODER_REVOLUTION / (0.5 * math.pi)


class PhysicsEngine:
    def __init__(self, physics_controller):
        """
        :param physics_controller: `pyfrc.physics.core.Physics` object
                                   to communicate simulation effects to
        """

        self.fl_encoder = self.fr_encoder = self.rl_encoder = self.rr_encoder = 0
        self.wrist_encoder = 0
        self.physics_controller = physics_controller

        """
        # Change these parameters to fit your robot!
        """

        # Create a lift simulation
        self.lift_motion = motion.LinearMotion("Lift", 6, 360)

        self.mecaum_drivetrain = drivetrains.MecanumDrivetrain(
            x_wheelbase=2, y_wheelbase=2, speed=5
        )

        self.tank_drivetrain = drivetrains.FourMotorDrivetrain(x_wheelbase=2, speed=5)

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
        front_l = hal_data["CAN"][2]["value"]
        front_r = -hal_data["CAN"][3]["value"]
        rear_l = hal_data["CAN"][4]["value"]
        rear_r = -hal_data["CAN"][5]["value"]

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
        hal_data["CAN"][2]["quad_position"] = int(self.fl_encoder * ENCODER_TICKS)
        hal_data["CAN"][4]["quad_position"] = int(self.fr_encoder * ENCODER_TICKS)
        hal_data["CAN"][3]["quad_position"] = int(self.rl_encoder * ENCODER_TICKS)
        hal_data["CAN"][5]["quad_position"] = int(self.rr_encoder * ENCODER_TICKS)

        # Simulate the lift encoders
        hal_data["encoder"][0]["count"] = self.lift_motion.compute(
            hal_data["CAN"][8]["value"], tm_diff
        )

        # Simulate the wrist encoders
        self.wrist_encoder += hal_data["CAN"][10]["value"] * tm_diff * 1000
        hal_data["encoder"][1]["count"] = self.wrist_encoder
        hal_data["encoder"][1]["distance_per_pulse"] = 1
