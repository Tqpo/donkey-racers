"""
Lab 2 Part I - Motor & servo stress test
Donkey Racers

Runs the ESC (drive motor) and servo (steering) through a series of tests:
  1. Arm the ESC
  2. Steering sweep (servo only)
  3. Throttle ramp forward (motor only)
  4. Combination grid (every throttle value x every steering value)
  5. Rapid changes (quick jumps between extremes)
  6. Reverse (extra credit - uses the ESC's backward-mode protocol,
     switches forward <-> backward 3 times)

Run everything:        python3 motor_test.py
Run only reverse test: python3 motor_test.py --reverse

SAFETY: put the car up on something so the wheels spin freely.
Press Ctrl+C at any time and the car goes back to neutral.
"""

import sys
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# ---------------- SETTINGS (change these to match your car) ----------------

THROTTLE_CHANNEL = 0   # PCA column the ESC is plugged into
STEERING_CHANNEL = 1   # PCA column the servo is plugged into

FREQUENCY = 60         # PWM frequency in Hz (60 Hz = one pulse every ~16.67 ms)

# Pulse widths in milliseconds
NEUTRAL = 1.5          # stopped / wheels straight
THROTTLE_MAX = 1.7     # top forward speed for the test (raise slowly, max 2.0)
REVERSE_SPEED = 1.35   # backward speed once in backward mode (1.0 - 1.5)
STEER_LEFT = 1.2       # full left  (widen toward 1.0 if your servo allows)
STEER_RIGHT = 1.8      # full right (widen toward 2.0 if your servo allows)

# ----------------------------------------------------------------------------

i2c = busio.I2C(board.SCL, board.SDA)   # open the I2C bus on the Pi
pca = PCA9685(i2c)                      # talk to the PCA board (address 0x40)
pca.frequency = FREQUENCY

PERIOD_MS = 1000 / FREQUENCY            # length of one PWM cycle in ms


def set_pulse(channel, ms):
    """Send a pulse of `ms` milliseconds on a PCA channel.

    The PCA wants a 16-bit duty cycle (0-65535), i.e. what fraction of
    each cycle the signal is high. So 1.5 ms out of 16.67 ms ~= 9% ~= 5898.
    """
    duty = int(ms / PERIOD_MS * 0xFFFF)
    pca.channels[channel].duty_cycle = duty


def throttle(ms):
    set_pulse(THROTTLE_CHANNEL, ms)


def steer(ms):
    set_pulse(STEERING_CHANNEL, ms)


def neutral(hold=0.5):
    """Stop the motor and center the wheels."""
    throttle(NEUTRAL)
    steer(NEUTRAL)
    time.sleep(hold)


def frange(start, stop, step):
    """Like range(), but for decimals. Includes `stop`."""
    values = []
    x = start
    while x <= stop + 1e-9:
        values.append(round(x, 3))
        x += step
    return values


# ---------------------------- TESTS ----------------------------------------

def arm_esc():
    print("\n[1] Arming ESC (holding neutral for 2 s)...")
    neutral(hold=2)


def steering_sweep():
    print("\n[2] Steering sweep")
    for ms in frange(STEER_LEFT, STEER_RIGHT, 0.1):
        print(f"    steer = {ms} ms")
        steer(ms)
        time.sleep(0.4)
    for ms in reversed(frange(STEER_LEFT, STEER_RIGHT, 0.1)):
        steer(ms)
        time.sleep(0.2)
    neutral()


def throttle_ramp():
    print("\n[3] Throttle ramp forward")
    for ms in frange(NEUTRAL, THROTTLE_MAX, 0.05):
        print(f"    throttle = {ms} ms")
        throttle(ms)
        time.sleep(0.8)
    for ms in reversed(frange(NEUTRAL, THROTTLE_MAX, 0.05)):
        throttle(ms)
        time.sleep(0.3)
    neutral()


def combination_grid():
    print("\n[4] Combination grid (throttle x steering)")
    throttle_values = frange(NEUTRAL, THROTTLE_MAX, 0.1)
    steering_values = [STEER_LEFT, NEUTRAL, STEER_RIGHT]
    for t in throttle_values:
        for s in steering_values:
            print(f"    throttle = {t} ms, steer = {s} ms")
            throttle(t)
            steer(s)
            time.sleep(0.8)
    neutral()


def rapid_changes():
    print("\n[5] Rapid changes")
    for _ in range(5):
        steer(STEER_LEFT)
        throttle(THROTTLE_MAX)
        time.sleep(0.3)
        steer(STEER_RIGHT)
        throttle(NEUTRAL)
        time.sleep(0.3)
    neutral()


MODE_SWITCH_HOLD = 0.2   # seconds to hold each pulse while switching modes
                         # (raise to 0.5 if your ESC doesn't switch)


def enter_backward_mode():
    """Protocol from the lab: neutral -> pulse between 1-1.5 ms -> neutral.
    After this, pulses between 1-1.5 ms drive the car backward."""
    throttle(NEUTRAL)
    time.sleep(MODE_SWITCH_HOLD)
    throttle(1.3)
    time.sleep(MODE_SWITCH_HOLD)
    throttle(NEUTRAL)
    time.sleep(MODE_SWITCH_HOLD)


def enter_forward_mode():
    """Protocol from the lab: neutral -> pulse between 1.5-2 ms -> neutral.
    After this, pulses between 1.5-2 ms drive the car forward."""
    throttle(NEUTRAL)
    time.sleep(MODE_SWITCH_HOLD)
    throttle(1.6)
    time.sleep(MODE_SWITCH_HOLD)
    throttle(NEUTRAL)
    time.sleep(MODE_SWITCH_HOLD)


def drive_backward(seconds):
    """Ramp up backward speed, hold it, then ramp back down to neutral.
    Lower pulse = faster backward, so we count DOWN from neutral."""
    print(f"    <<< BACKWARD (up to {REVERSE_SPEED} ms)")
    for ms in reversed(frange(REVERSE_SPEED, NEUTRAL, 0.05)):
        throttle(ms)
        time.sleep(0.3)
    time.sleep(seconds)
    for ms in frange(REVERSE_SPEED, NEUTRAL, 0.05):
        throttle(ms)
        time.sleep(0.2)


def drive_forward(seconds, top=1.65):
    """Ramp up forward speed, hold it, then ramp back down to neutral."""
    print(f"    >>> FORWARD (up to {top} ms)")
    for ms in frange(NEUTRAL, top, 0.05):
        throttle(ms)
        time.sleep(0.3)
    time.sleep(seconds)
    for ms in reversed(frange(NEUTRAL, top, 0.05)):
        throttle(ms)
        time.sleep(0.2)


def reverse_test(cycles=3):
    """Switch between forward and backward several times so both
    directions are clearly visible on video."""
    print("\n[6] Reverse (extra credit)")
    for i in range(1, cycles + 1):
        print(f"  cycle {i} of {cycles}")

        enter_backward_mode()
        drive_backward(seconds=2)
        time.sleep(1)               # pause at neutral so the switch is obvious

        enter_forward_mode()
        drive_forward(seconds=2)
        time.sleep(1)
    neutral()


# ---------------------------- MAIN -----------------------------------------

def main():
    print("Motor/servo stress test - wheels should be OFF the ground.")
    print(f"ESC on channel {THROTTLE_CHANNEL}, servo on channel {STEERING_CHANNEL}")
    # Run with --reverse to skip straight to the reverse test (handy for filming)
    reverse_only = "--reverse" in sys.argv
    try:
        arm_esc()
        if not reverse_only:
            steering_sweep()
            throttle_ramp()
            combination_grid()
            rapid_changes()
        reverse_test()
        print("\nAll tests done!")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        # Always leave the car stopped, no matter what happened above
        neutral(hold=0.5)
        pca.deinit()
        print("Car set to neutral. Bye!")


if __name__ == "__main__":
    main()
