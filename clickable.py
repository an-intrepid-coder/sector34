class Clickable:
    def __init__(self, rect):
        self.rect = rect

    def clicked(self, pos):
        return self.rect[0] <= pos[0] < self.rect[0] + self.rect[2] and self.rect[1] <= pos[1] < self.rect[1] + \
            self.rect[3]

