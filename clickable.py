class Clickable:
    def __init__(self, rect, attachment = None):
        self.rect = rect
        self.attachment = attachment

    def clicked(self, pos):
        within_x = pos[0] >= self.rect[0] and pos[0] < self.rect[0] + self.rect[2]
        within_y = pos[1] >= self.rect[1] and pos[1] < self.rect[1] + self.rect[3]
        return within_x and within_y

