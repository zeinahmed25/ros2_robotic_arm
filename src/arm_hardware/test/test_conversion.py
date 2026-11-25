import math

from arm_hardware.conversion import format_command, interpolate, rad_to_servo_deg


def test_zero_maps_to_center():
    assert rad_to_servo_deg(0.0) == 90.0
    assert rad_to_servo_deg(0.0, center_deg=100.0) == 100.0


def test_positive_and_negative_angles():
    assert math.isclose(rad_to_servo_deg(math.pi / 4), 135.0)
    assert math.isclose(rad_to_servo_deg(-math.pi / 4), 45.0)


def test_invert_flips_direction():
    assert math.isclose(rad_to_servo_deg(math.pi / 4, invert=True), 45.0)


def test_clamped_to_servo_range():
    assert rad_to_servo_deg(math.pi) == 180.0
    assert rad_to_servo_deg(-math.pi) == 0.0


def test_format_command_rounds_and_clamps():
    assert format_command([90.2, 44.6]) == b'90,45\n'
    assert format_command([-5.0, 200.0]) == b'0,180\n'


def test_interpolate():
    assert interpolate([0.0, 10.0], [10.0, 20.0], 0.5) == [5.0, 15.0]
    assert interpolate([0.0], [10.0], 2.0) == [10.0]
    assert interpolate([0.0], [10.0], -1.0) == [0.0]
