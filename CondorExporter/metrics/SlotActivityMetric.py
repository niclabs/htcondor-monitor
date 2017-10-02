from prometheus_client.core import GaugeMetricFamily


class SlotActivityMetric:

    def __init__(self):
        self.idle = GaugeMetricFamily('condor_slot_activity_idle',
                                      'Is this slot idle', labels=['machine', 'slot', 'address'])
        self.busy = GaugeMetricFamily('condor_slot_activity_busy',
                                      'Is this slot busy', labels=['machine', 'slot', 'address'])

    def as_list(self):
        return [self.idle, self.busy]
