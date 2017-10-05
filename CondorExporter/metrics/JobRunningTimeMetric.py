from prometheus_client.core import GaugeMetricFamily


class JobRunningTimeMetric:
    def __init__(self):
        self.time = GaugeMetricFamily('condor_job_avg_running_time_seconds',
                                      'Average running time for completed jobs for the specific cluster and submitter',
                                      labels=['submitter', 'cluster', 'id'])

    def as_list(self):
        return [self.time]
