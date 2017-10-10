
class Machine:

    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.slots = {}

    def reset_slots_metrics(self):
        for slot in iter(self.slots.values()):
            slot.reset_metrics()

    def update_activity(self, activity_metric):
        for slot in iter(self.slots.values()):
            is_busy = slot.activity == "Busy"
            is_idle = slot.activity == "Idle"
            activity_metric.busy.add_metric([self.name, str(slot.slot_id), self.address], is_busy)
            activity_metric.idle.add_metric([self.name, str(slot.slot_id), self.address], is_idle)

    def update_state(self, state_metric):
        for slot in iter(self.slots.values()):
            is_owner = slot.state == "Owner"
            is_claimed = slot.state == "Claimed"
            is_unclaimed = slot.state == "Unclaimed"
            state_metric.owner.add_metric([self.name, str(slot.slot_id), self.address], is_owner)
            state_metric.claimed.add_metric([self.name, str(slot.slot_id), self.address], is_claimed)
            state_metric.unclaimed.add_metric([self.name, str(slot.slot_id), self.address], is_unclaimed)
