import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime

class OledHandler:
    def __init__(self):
        # 128x32 display with hardware I2C:
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=1, gpio=1) # setting gpio to 1 is hack to 
        # Initialize library.
        self.disp.begin()
        # Clear display.
        self.disp.clear()
        self.disp.display()
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height-self.padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0
        # Load default font.
        self.font = ImageFont.load_default()
        self.lines = ["", "", ""]
        
    def WriteLine(self, line, text):
        self.lines[line] = text

    def Update(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        now = datetime.now()
        DateStr=str(now.strftime("%Y/%m/%d %H:%M:%S"))
        self.draw.text((self.x, self.top), DateStr, font=self.font, fill=255)
        self.draw.text((self.x, self.top+8), str(self.lines[0]), font=self.font, fill=255)
        self.draw.text((self.x, self.top+16), str(self.lines[1]), font=self.font, fill=255)
        self.draw.text((self.x, self.top+24), str(self.lines[2]), font=self.font, fill=255)
        # Display image.
        self.disp.image(self.image)
        self.disp.display()