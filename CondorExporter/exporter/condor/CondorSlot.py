
class Slot:

    def __init__(self, slot_id):
        self.slot_id = slot_id
        self.activity = None
        self.state = None

    def reset_metrics(self):
        self.activity = None
        self.state = None
