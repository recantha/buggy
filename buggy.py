# Code for Brian Corteil's Tiny 4WD robot, based on code from Brian as modified by Emma Norling.
# Subsequently modified by Tom Oinn to add dummy functions when no explorer hat is available,
# use any available joystick, use the new function in 1.0.6 of approxeng.input to get multiple
# axis values in a single call, use implicit de-structuring of tuples to reduce verbosity, add
# an exception to break out of the control loop on pressing HOME etc.

from time import sleep
from board import SCL, SDA
from gpiozero import Button, RGBLED
from adafruit_ssd1306 import SSD1306_I2C
import os
from busio import I2C
import subprocess
from PIL import Image, ImageDraw, ImageFont

font_size = 8
line_0 = ''
line_1 = ''
line_2 = ''
line_3 = ''

# Display stuff
def update_display():
    global disp, font, image, draw, width, font_size
    global line_0, line_1, line_2, line_3

    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    disp.show()

    draw.text((0, 0), line_0, font=font, fill=255)
    draw.text((0, font_size), line_1, font=font, fill=255)
    draw.text((0, 2*font_size), line_2, font=font, fill=255)
    draw.text((0, 3*font_size), line_3, font=font, fill=255)
    disp.image(image)
    disp.show()

def battery_monitor():
    global line_1

    print('Battery monitor updating')
    cmd = "python3 /home/pi/RedBoard/system/bat_check.py"
    bat = subprocess.check_output(cmd, shell = True ).decode()
    line_1 = ''
    update_display()
    sleep(0.25)
    line_1 = 'Batt: ' + str(bat)
    update_display()

try:
    # Define display
    i2c = I2C(SCL, SDA)
    disp = SSD1306_I2C(128, 32, i2c)

    # Clear display
    disp.fill(0)
    disp.show()

    font = ImageFont.truetype('/home/pi/RedBoard/system/Greenscr.ttf', font_size)

    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

except Exception as X:
    print('Unable to set-up display')
    print(X)

# Get hostname and display it
try:
    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
    line_0 = 'IP:' + IP
    update_display()

    battery_monitor()

except:
    print('Failed to do anything with the display')

try:
    # Attempt to import the Explorer HAT library. If this fails, because we're running somewhere
    # that doesn't have the library, we create dummy functions for set_speeds and stop_motors which
    # just print out what they'd have done. This is a fairly common way to deal with hardware that
    # may or may not exist! Obviously if you're actually running this on one of Brian's robots you
    # should have the Explorer HAT libraries installed, this is really just so I can test on my big
    # linux desktop machine when coding.

    import redboard

    print('RedBoard library available.')

    reset_button = Button(17)

    def set_speeds(power_left, power_right):
        """
        As we have an motor hat, we can use the motors
        :param power_left: 
            Power to send to left motor
        :param power_right: 
            Power to send to right motor
        """
        #print('Left: {}, Right: {}'.format(power_left, power_right))
        redboard.M1(power_right)
        redboard.M2(power_left)


    def stop_motors():
        """
        As we have an motor hat, stop the motors using their motors call
        """
        print('Motors stopped!')
        redboard.M2(0)
        redboard.M1(0)

    def shutdown():
        print('Shutting down')
        os.system('sudo shutdown -h now')
        sleep(1)
        print('Exiting the script')
        exit()

except ImportError:

    print('No explorer HAT library available, using dummy functions.')


    def set_speeds(power_left, power_right):
        """
        No motor hat - print what we would have sent to it if we'd had one.
        """
        print('Left: {}, Right: {}'.format(power_left, power_right))
        sleep(0.1)


    def stop_motors():
        """
        No motor hat, so just print a message.
        """
        print('Motors stopping')

# All we need, as we don't care which controller we bind to, is the ControllerResource
from approxeng.input.selectbinder import ControllerResource


class RobotStopException(Exception):
    """
    The simplest possible subclass of Exception, we'll raise this if we want to stop the robot
    for any reason. Creating a custom exception like this makes the code more readable later.
    """
    pass

class PiResetException(Exception):
    pass

def mixer(yaw, throttle, max_power=100):
    """
    Mix a pair of joystick axes, returning a pair of wheel speeds. This is where the mapping from
    joystick positions to wheel powers is defined, so any changes to how the robot drives should
    be made here, everything else is really just plumbing.
    
    :param yaw: 
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle: 
        Throttle axis value, ranges from -1.0 to 1.0
    :param max_power: 
        Maximum speed that should be returned from the mixer, defaults to 100
    :return: 
        A pair of power_left, power_right integer values to send to the motor driver
    """
    left = throttle + yaw
    right = throttle - yaw
    scale = float(max_power) / max(1, abs(left), abs(right))
    return int(left * scale), int(right * scale)


# Outer try / except catches the RobotStopException we just defined, which we'll raise when we want to
# bail out of the loop cleanly, shutting the motors down. We can raise this in response to a button press
try:
    max_power = 80
    min_power = 0
    current_power = 20

    reset_button.when_pressed = shutdown

    # Pulse RGB LED to show Bluetooth connection waiting
    led = RGBLED(red=26, green=16, blue=19)
    blue = (0,0,1)
    black = (0, 0, 0)
    led.pulse(on_color=blue, off_color=black)

    while True:
        # Inner try / except is used to wait for a controller to become available, at which point we
        # bind to it and enter a loop where we read axis values and send commands to the motors.
        try:
            # Bind to any available joystick, this will use whatever's connected as long as the library
            # supports it.
            with ControllerResource(dead_zone=0.3, hot_zone=0.5) as joystick:
                line_2 = 'Controller found'
                update_display()
                sleep(2)
                line_2 = 'Power:' + str(current_power)
                update_display()

                # Turn off LED indicator
                led.off()
                led.color = (0, 0.7, 0)

                # Loop until the joystick disconnects, or we deliberately stop by raising a
                # RobotStopException
                while joystick.connected:
                    # Get joystick values from the left analogue stick
                    x_axis, y_axis = joystick['lx', 'ly']
                    # Get power from mixer function
                    power_left, power_right = mixer(yaw=x_axis, throttle=y_axis, max_power=current_power)
                    # Set motor speeds
                    set_speeds(power_left, power_right)
                    # Get a ButtonPresses object containing everything that was pressed since the last
                    # time around this loop.
                    joystick.check_presses()
                    # Print out any buttons that were pressed, if we had any
                    if joystick.has_presses:
                        print(joystick.presses)

                    # If X was pressed, raise a RobotStopException to bail out of the loop
                    if 'home' in joystick.presses:
                        stop_motors()

                    if 'cross' in joystick.presses:
                        line_3 = 'Program exit?'
                        update_display()
                        sleep(2)
                        joystick.check_presses()
                        if 'start' in joystick.presses:
                            line_3 = 'Exiting program'
                            update_display()
                            raise RobotStopException()
                        else:
                            line_3 = "Aborting exit"
                            update_display()
                            sleep(0.5)
                            line_3 = ""
                            update_display()

                    if 'circle' in joystick.presses:
                        line_3 = 'Reset the Pi?'
                        update_display()
                        sleep(2)
                        joystick.check_presses()
                        if 'start' in joystick.presses:
                            line_3 = 'Resetting'
                            update_display()
                            raise PiResetException()
                        else:
                            line_3 = "Aborting reset"
                            update_display()
                            sleep(0.5)
                            line_3 = ""
                            update_display()

                    if 'triangle' in joystick.presses:
                        battery_monitor()

                    if 'l1' in joystick.presses:
                        current_power = current_power - 10
                        line_2 = 'Power:' + str(current_power)
                        update_display()
                        print('Current power set to {}'.format(current_power))

                    if 'r1' in joystick.presses:
                        current_power = current_power + 10
                        line_2 = 'Power:' + str(current_power)
                        update_display()
                        print('Current power set to {}'.format(current_power))

                    if current_power > max_power:
                        current_power = max_power
                        line_2 = 'Power:' + str(current_power)
                        update_display()
                        print('Current power ceilinged at {}'.format(current_power))

                    if current_power < min_power:
                        current_power = min_power
                        line_2 = 'Power:' + str(current_power)
                        update_display()
                        print('Current power floored at {}'.format(current_power))

        except IOError:
            # We get an IOError when using the ControllerResource if we don't have a controller yet,
            # so in this case we just wait a second and try again after printing a message.
            line_2 = 'No controller found yet'
            update_display()
            sleep(0.5)

except RobotStopException:
    # This exception will be raised when the Cross button is pressed
    # AND THEN the Options button is pressed. At which point we should
    # stop the motors.
    stop_motors()
    line_3 = 'Program exit'
    update_display()
    sleep(2)

except PiResetException:
    # This exception will be raised when the Circle button is pressed
    # AND THEN the Options button is pressed, at which point we should
    # stop the motors and reset the Pi
    stop_motors()
    line_3 = 'Resetting the Pi'
    update_display()
    sleep(2)
    subprocess.call(["sudo", "shutdown", "-r", "now"])

