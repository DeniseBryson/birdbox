class GPIO:
    BCM = "BCM"
    BOARD = "BOARD"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0

    @staticmethod
    def setmode(mode):
        print(f"GPIO.setmode({mode})")

    @staticmethod
    def setup(channel, state):
        print(f"GPIO.setup(channel={channel}, state={state})")

    @staticmethod
    def output(channel, state):
        print(f"GPIO.output(channel={channel}, state={state})")

    @staticmethod
    def cleanup():
        print("GPIO.cleanup()")
