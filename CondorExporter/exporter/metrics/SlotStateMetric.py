from prometheus_client.core import GaugeMetricFamily


class SlotStateMetric:
    def __init__(self):
        self.owner = GaugeMetricFamily('condor_slot_state_owner',
                                       'Is this slot in the owner state', labels=['machine', 'slot', 'address'])
        self.claimed = GaugeMetricFamily('condor_slot_state_claimed',
                                         'Is this slot in the claimed state', labels=['machine', 'slot', 'address'])
        self.unclaimed = GaugeMetricFamily('condor_slot_state_unclaimed',
                                           'Is this slot in the unclaimed state', labels=['machine', 'slot', 'address'])

    def as_list(self):
        return [self.owner, self.claimed, self.unclaimed]
