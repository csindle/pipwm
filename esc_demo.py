#!/usr/bin/env python3

import time
import pigpio


class TurnigyESC:
    """
    Turnigy Electonic Speed controller.
    Tested with:
      Plush 30 A
    """
    ## YMMV
    MIN_WIDTH = 650

    # Note that some batteries, 12 volt PSUs, etc. might only be capable of far less than this (e.g. 1350)
    # However, the controllers range should still be set to max for finest full-scale resolution.
    MAX_WIDTH = 2400

    def __init__(self, pin):
        self.conn = pigpio.pi()
        self.pin = pin

    def pwm(self, width: int, snooze: int = 0) -> None:
        """
        Convenience wrapper around pigpio's set_servo_pulsewidth.
        width: The servo pulsewidth in microseconds. 0 switches pulses off.
        snooze: seconds before returning.
        """
        print("Setting pulse width to", width, "microseconds for", snooze, "seconds.")
        self.conn.set_servo_pulsewidth(self.pin, width)
        if snooze:
            time.sleep(snooze)
        return

    def calibrate(self) -> None:
        """
        This trains the ESC on the full scale (max - min range) of the controller / pulse generator.
        This only needs to be done when changing controllers, transmitters, etc. not upon every power-on.
        NB: if already calibrated, full throttle will be applied (briefly)!  Disconnect propellers, etc.
        """
        print("Calibrating...")
        self.pwm(width=self.MAX_WIDTH)
        input("Connect power and press Enter to calibrate...")
        self.pwm(width=self.MAX_WIDTH, snooze=2)   # Official docs: "about 2 seconds".
        self.pwm(width=self.MIN_WIDTH, snooze=4)   # Time enough for the cell count, etc. beeps to play.
        print("Finished calibration.")

    def arm(self) -> None:
        """
        Arms the ESC. Required upon every power cycle.
        """
        print("Arming...")
        self.pwm(width=self.MIN_WIDTH, snooze=4)  # Time enough for the cell count, etc. beeps to play.
        print("Armed...")

    def halt(self) -> None:
        """
        Switch of the GPIO, and un-arm the ESC.
        Ensure this runs, even on unclean shutdown.
        """
        print("Slowing...")
        self.pwm(width=self.MIN_WIDTH, snooze=1)   # This 1 sec seems to *hasten* shutdown.
        print("Failsafe...")
        self.pwm(0)
        print("Disabling GPIO.")
        self.conn.stop()
        print("Halted.")

    def test(self) -> None:
        """
        Test with a triangularish wave.
        Useful for determining the max and min PWM values.
        """
        max_width = self.MAX_WIDTH - 1330  # microseconds
        min_width = self.MIN_WIDTH + 80    # microseconds
        step = 9  # microseconds

        snooze = 0.3  # seconds

        input("Press Enter to conduct run-up test...")
        for i in range(1):
            print("Increasing...")
            for width in range(min_width, max_width, step):
                self.pwm(width=width, snooze=snooze)

        time.sleep(1)  # Duration test.  Seems to last almost 60s @ 1350.

        print("Holding at max...")
        snooze = 0.1
        print("Decreasing...")
        for width in range(max_width, min_width, -step):
            self.pwm(width=width, snooze=snooze)


if __name__ == "__main__":

    esc = TurnigyESC(pin=4)
    try:
        #esc.calibrate()  # Recommended when changing "transmitter" or controller.
        esc.arm()         # Required upon every power-up.
        esc.test()        # Run-up test.
    except KeyboardInterrupt:
        pass
    finally:
        esc.halt()
