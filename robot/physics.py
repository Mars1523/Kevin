from pyfrc.physics import drivetrains

ENCODER_REVOLUTION = 360


class PhysicsEngine:
    def __init__(self, physics_controller):
        """
        :param physics_controller: `pyfrc.physics.core.Physics` object
                                   to communicate simulation effects to
        """

        self.physics_controller = physics_controller

        """
        # Change these parameters to fit your robot!
        """

        self.mecaum_drivetrain = drivetrains.MecanumDrivetrain(
            x_wheelbase=2, y_wheelbase=2, speed=5
        )

        self.tank_drivetrain = drivetrains.FourMotorDrivetrain(x_wheelbase=2, speed=5)

    def update_sim(self, hal_data, now, tm_diff):
        """
        Called when the simulation parameters for the program need to be
        updated.

        :param now: The current time as a float
        :param tm_diff: The amount of time that has passed since the last
                        time that this function was called
        """

        is_tank = hal_data["solenoid"][1]["value"]

        # Simulate the drivetrain
        # right motors must be inverted
        front_l = hal_data["CAN"][2]["value"]
        front_r = -hal_data["CAN"][3]["value"]
        rear_l = hal_data["CAN"][4]["value"]
        rear_r = -hal_data["CAN"][5]["value"]

        if is_tank:
            speed, rotation = self.tank_drivetrain.get_vector(
                rear_l, rear_r, front_l, front_r
            )
            self.physics_controller.drive(speed, rotation, tm_diff)
        else:
            x_speed, y_speed, rotation = self.mecaum_drivetrain.get_vector(
                rear_l, rear_r, front_l, front_r
            )
            self.physics_controller.vector_drive(x_speed, y_speed, rotation, tm_diff)
