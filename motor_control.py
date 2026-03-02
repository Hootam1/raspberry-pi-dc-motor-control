#!/usr/bin/env python3
import pygame
import RPi.GPIO as GPIO
import time

# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BCM)

# PWM Pins
TURN_R_L = 20   # Pin 38
TURN_R_R = 21   # Pin 40
TURN_L_L = 16   # Pin 36
TURN_L_R = 12   # Pin 32

GPIO.setup(TURN_R_L, GPIO.OUT)
GPIO.setup(TURN_R_R, GPIO.OUT)
GPIO.setup(TURN_L_L, GPIO.OUT)
GPIO.setup(TURN_L_R, GPIO.OUT)

pwm_r_l = GPIO.PWM(TURN_R_L, 2000)
pwm_r_r = GPIO.PWM(TURN_R_R, 2000)
pwm_l_l = GPIO.PWM(TURN_L_L, 2000)
pwm_l_r = GPIO.PWM(TURN_L_R, 2000)

pwm_r_l.start(0)
pwm_r_r.start(0)
pwm_l_l.start(0)
pwm_l_r.start(0)

# Direction Pins
DIR_UP = 15
DIR_DOWN = 18

GPIO.setup(DIR_UP, GPIO.OUT)
GPIO.setup(DIR_DOWN, GPIO.OUT)

# ---------------- CONTROLLER SETUP ----------------
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()

print("Controller Connected")

base_speed = 50

# ---------------- MAIN LOOP ----------------
try:
    while True:
        pygame.event.pump()

        axis1 = controller.get_axis(1)  # L3 up/down
        axis3 = controller.get_axis(3)  # R3 left/right

        R1 = controller.get_button(5)
        L1 = controller.get_button(4)

        # -------- SPEED CONTROL --------
        if R1:
            base_speed = min(100, base_speed + 1)
            print("Speed:", base_speed)
            time.sleep(0.1)

        if L1:
            base_speed = max(0, base_speed - 1)
            print("Speed:", base_speed)
            time.sleep(0.1)

        slow_speed = base_speed * 0.1

        # -------- JOYSTICK CONTROL (NO DOUBLE SIGNAL) --------
        turning_active = abs(axis3) > 0.5
        forward_active = abs(axis1) > 0.5

        # If BOTH joysticks are moved → ignore L3
        if turning_active and forward_active:
            forward_active = False

        # ---- TURNING ----
        if turning_active:

            # Stop forward/backward
            GPIO.output(DIR_UP, GPIO.LOW)
            GPIO.output(DIR_DOWN, GPIO.LOW)

            if axis3 > 0.5:  # RIGHT
                pwm_r_l.ChangeDutyCycle(base_speed)
                pwm_r_r.ChangeDutyCycle(slow_speed)
                pwm_l_l.ChangeDutyCycle(0)
                pwm_l_r.ChangeDutyCycle(0)

            elif axis3 < -0.5:  # LEFT
                pwm_r_l.ChangeDutyCycle(0)
                pwm_r_r.ChangeDutyCycle(0)
                pwm_l_l.ChangeDutyCycle(slow_speed)
                pwm_l_r.ChangeDutyCycle(base_speed)

        # ---- FORWARD / BACKWARD ----
        elif forward_active:

            # Stop turning
            pwm_r_l.ChangeDutyCycle(0)
            pwm_r_r.ChangeDutyCycle(0)
            pwm_l_l.ChangeDutyCycle(0)
            pwm_l_r.ChangeDutyCycle(0)

            if axis1 < -0.5:  # UP
                GPIO.output(DIR_UP, GPIO.HIGH)
                GPIO.output(DIR_DOWN, GPIO.LOW)

            elif axis1 > 0.5:  # DOWN
                GPIO.output(DIR_UP, GPIO.LOW)
                GPIO.output(DIR_DOWN, GPIO.HIGH)

        # ---- NOTHING PRESSED ----
        else:
            pwm_r_l.ChangeDutyCycle(0)
            pwm_r_r.ChangeDutyCycle(0)
            pwm_l_l.ChangeDutyCycle(0)
            pwm_l_r.ChangeDutyCycle(0)

            GPIO.output(DIR_UP, GPIO.LOW)
            GPIO.output(DIR_DOWN, GPIO.LOW)

        time.sleep(0.02)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pwm_r_l.stop()
    pwm_r_r.stop()
    pwm_l_l.stop()
    pwm_l_r.stop()
    GPIO.cleanup()
    pygame.quit()