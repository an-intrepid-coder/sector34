class ConsoleLog: 
    def __init__(self):
        self.messages = []

    def push(self, msg, attachment = None):
        line = {"msg": msg, "attachment": attachment}
        self.messages.append(line)

