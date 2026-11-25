"""Pure helper functions (no ROS imports) so they can be unit-tested anywhere."""
import math


def rad_to_servo_deg(angle_rad, center_deg=90.0, invert=False):
    """Convert a joint angle in radians to a servo angle in degrees.

    A joint angle of 0 rad maps to ``center_deg``. The result is clamped to
    the 0..180 degree range of a hobby servo.
    """
    sign = -1.0 if invert else 1.0
    deg = center_deg + sign * math.degrees(angle_rad)
    return min(180.0, max(0.0, deg))


def format_command(servo_degs):
    """Build the serial line for the firmware, e.g. [90.2, 44.6] -> '90,45\\n'."""
    values = [int(round(min(180.0, max(0.0, d)))) for d in servo_degs]
    return (','.join(str(v) for v in values) + '\n').encode('ascii')


def interpolate(start, target, fraction):
    """Linear interpolation between two lists of numbers, fraction in 0..1."""
    f = min(1.0, max(0.0, fraction))
    return [s + (t - s) * f for s, t in zip(start, target)]
