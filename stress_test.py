import board
from adafruit_pca9685 import PCA9685
import time
import itertools
import random

i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 50
print("connected")