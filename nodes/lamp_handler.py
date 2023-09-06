import Jetson.GPIO as GPIO
from enum import Enum

class Color(Enum):
    RED = 0
    GRN = 1
    BUZZER = 2

class LampState(Enum):
    OFF = 0
    ON = 1
    BLINK = 2

class Lamp:
    def __init__(self, color, pinNum):
        self.color = color
        self.pin = pinNum
        self.state = LampState.OFF
        self.onoff = False
        self.cnt = 0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        print("Lamp setup")

    def On(self):
        self.onoff = True
        GPIO.output(self.pin, self.onoff)
    
    def Off(self):
        self.onoff = False
        GPIO.output(self.pin, self.onoff)

    def Toggle(self):
        self.onoff = not self.onoff
        GPIO.output(self.pin, self.onoff)
        #print("Toggle {}, {}".format(self.pin, self.onoff))
    
    def SetState(self, state):
        self.state = state
        self.cnt = 0

class LampHandler:
    def __init__(self):
        print("GPIO Set mode")
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        self.lamps = [ Lamp(Color.RED, 11),
                        Lamp(Color.GRN, 15),
                        Lamp(Color.BUZZER, 12)]

    def Update_5Hz(self):
        for i in range(len(self.lamps)):
            if self.lamps[i].state == LampState.BLINK:
                self.lamps[i].cnt += 1
                if self.lamps[i].cnt>2:
                    self.lamps[i].cnt = 0
                    self.lamps[i].Toggle()
            elif self.lamps[i].state == LampState.ON:
                self.lamps[i].On()
            elif self.lamps[i].state == LampState.OFF:
                self.lamps[i].Off()
    
    def SetState(self, color, state):
        if color == Color.RED:
            self.lamps[0].SetState(state)
        elif color == Color.GRN:
            self.lamps[1].SetState(state)
        elif color == Color.BUZZER:
            self.lamps[2].SetState(state)


