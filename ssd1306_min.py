import time
import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
try:
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
except ValueError: 
    print('')
    print('SSD1306 OLED Screen not found')
    print('')
    exit()


# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
#font = ImageFont.load_default()
font = ImageFont.truetype('/home/pi/RedBoard/system/Greenscr.ttf', 12)

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
#font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)

while True:

    try:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")

        cmd = "python3 /home/pi/RedBoard/system/bat_check.py"    
        bat = subprocess.check_output(cmd, shell = True ).decode()
        #print (bat)

        # Write two lines of text.

        #draw.text((x, top+0), "IP: "+IP, font=font, fill=255)
        draw.text((0, 2),      str(IP),  font=font, fill=255)
        draw.text((x, 16),     "BAT: " + str(bat), font=font, fill=255)

        # Display image.
        disp.image(image)
        disp.show()
        time.sleep(.1)

    except KeyboardInterrupt: 
        print ("exit")
        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        disp.image(image)
        disp.show()
        time.sleep(0.5)
        exit()

