class ConsoleLog: 
    def __init__(self):
        self.messages = []

    def push(self, msg):
        self.messages.append(msg)

