#!/usr/bin/python

import argparse
import time

import htcondor
import re
from exporter.condor import CondorJobCluster
from exporter.condor import Machine
from exporter.condor import Slot
from exporter.condor import CondorJob
from exporter.metrics.JobRunningTimeMetric import JobRunningTimeMetric
from exporter.metrics.JobStateMetric import JobStateMetric
from exporter.metrics.SlotStateMetric import SlotStateMetric
from exporter.metrics.SlotActivityMetric import SlotActivityMetric

from prometheus_client import start_wsgi_server
from prometheus_client.core import REGISTRY



def parse_address(address):
#   regex_match = re.compile(r'.*p="primary"; a="([\d.]*)"; port.*}').match(address)
    regex_match = re.compile(r'<(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}):.*').match(address)
    if regex_match is not None:
        return regex_match.group(1)
    return ""


def parse_submitter(user):
    # User is a string in the form "username@machine" we want only the 'machine' part
    regex_match = re.compile(r'.*@(.*)$').match(user)
    if regex_match is not None:
        return regex_match.group(1)
    return ""


def get_cluster_history(schedd, cluster):
    requirements = 'Machine =?= %s && ClusterId == %d' % (cluster.submitter, cluster.cluster_id)
    projection = ["Owner", "ExitStatus", "ProcId", "JobStatus", "RemoteSlotID", "RemoteHost", "RemoteWallClockTime"]
    jobs = schedd.history(requirements, projection)
    for job in jobs:
        job_id = job.get("ProcId", -1)
        status = job.get("JobStatus", "")
        runtime = job.get("RemoteWallClockTime", 0)
        if job not in cluster.jobs:
            cluster.jobs[job_id] = CondorJob(job_id)
        current_job = cluster.jobs[job_id]
        current_job.state = parse_job_status(status)
        current_job.running_time = runtime


def parse_job_status(status_code):
    if status_code == 1:
        return "Idle"
    elif status_code == 2:
        return "Running"
    elif status_code == 5:
        return "Held"
    elif status_code == 4:
        return "Completed"
    return ""


class CondorCollector(object):

    def __init__(self, pool=None):
        self.machines = {}
        self.clusters = {}
        self.inactive_clusters = []
        self.coll = htcondor.Collector(pool)

    def query_all_slots(self, projection=[]):
        all_submitters_query = self.coll.query(htcondor.AdTypes.Startd, projection=projection)
        return all_submitters_query

    def get_all_submitters(self):
        projection = ["Name", "MyAddress"]
        all_submitters_query = self.coll.query(htcondor.AdTypes.Submitter, projection=projection)
        schedds = []
        for submitter in all_submitters_query:
            schedds.append(htcondor.Schedd(submitter))
        return schedds

    def get_machine_list(self):
        return [machine for machine in iter(self.machines.values())]

    def query_all_machines(self):
        projection = ["Machine", "State", "Name", "SlotID", "Activity", "MyAddress"]
        slots_info = self.query_all_slots(projection=projection)
        for slot in slots_info:
            name = slot.get("Machine", None)
            slot_id = slot.get("SlotID", None)
            activity = slot.get("Activity", None)
            state = slot.get("State", None)
            address = parse_address(slot.get("MyAddress", ""))
            if name not in self.machines:
                self.machines[name] = Machine(name, address)
            current_machine = self.machines[name]
            current_machine.address = address
            if slot_id not in current_machine.slots:
                current_machine.slots[slot_id] = Slot(slot_id)
            current_slot = current_machine.slots[slot_id]
            current_slot.activity = activity
            current_slot.state = state
        return self.get_machine_list()

    def collect_machine_metrics(self, activity_metrics, state_metrics):
        for machine in iter(self.machines.values()):
            machine.reset_slots_metrics()
        machines = self.query_all_machines()
        for machines in machines:
            machines.update_activity(activity_metrics)
            machines.update_state(state_metrics)

    def get_jobs_from_schedd(self, schedd):
        projection = ["Owner", "User", "ExitStatus", "Cmd", "ClusterId", "ProcId",
                      "GlobalJobId", "JobStatus", "RemoteSlotID", "RemoteHost"]
        # requirements = 'Machine =?= %s' % submitter.name
        try:
            jobs_from_submitter = schedd.xquery(projection=projection)
        except RuntimeError:
            return []
        for job in jobs_from_submitter:
            cluster_id = job.get("ClusterId", None)
            job_id = job.get("ProcId", None)
            status = job.get("JobStatus", None)
            submitter = job.get("User", "")
            if cluster_id not in self.clusters:
                self.clusters[cluster_id] = CondorJobCluster(cluster_id, parse_submitter(submitter))
            if job_id not in self.clusters[cluster_id].jobs:
                self.clusters[cluster_id].jobs[job_id] = CondorJob(job_id)
            self.clusters[cluster_id].jobs[job_id].state = parse_job_status(status)
            if self.clusters[cluster_id].jobs[job_id].state == "Running":
                self.clusters[cluster_id].jobs[job_id].execute_machine = job.get("RemoteHost", "")
        for cluster in iter(self.clusters.values()):
            get_cluster_history(schedd, cluster)
        return [cluster for cluster in iter(self.clusters.values())]

    def collect_job_metrics(self, job_state_metrics, job_time_metrics):
        for cluster, ttl in self.inactive_clusters:
            cluster.update_job_state(job_state_metrics)
            cluster.update_job_running_time(job_time_metrics)
        submitter_schedds = self.get_all_submitters()
        for submitter in submitter_schedds:
            for job in self.get_jobs_from_schedd(submitter):
                job.update_job_state(job_state_metrics)
                job.update_job_running_time(job_time_metrics)
        # Remove inactive cluster from main list, add them to inactive cluster list
        for cluster in iter(self.clusters.values()):
            if not cluster.is_active():
                self.inactive_clusters.append((cluster, 6))
        # Decrease time to live for all inactive clusters and remove old inactive clusters

        self.inactive_clusters = [(cluster, i-1) for cluster, i in self.inactive_clusters if i > 0]
        for cluster, ttl in self.inactive_clusters:
            if cluster.cluster_id in self.clusters:
                del self.clusters[cluster.cluster_id]

    def collect(self):
        activity_metrics = SlotActivityMetric()
        state_metrics = SlotStateMetric()
        job_state_metrics = JobStateMetric()
        job_time_metrics = JobRunningTimeMetric()
        metrics = [activity_metrics, state_metrics, job_state_metrics, job_time_metrics]

        self.collect_machine_metrics(activity_metrics, state_metrics)
        self.collect_job_metrics(job_state_metrics, job_time_metrics)
        metrics_list = []
        for m in metrics:
            metrics_list += m.as_list()
        for m in metrics_list:
            yield m


def main():
    parser = argparse.ArgumentParser(description="Run condor exporter to expose metrics for prometheus consumption")
    parser.add_argument('-p', '--port', type=int, default=9118, required=False,
                        help='Specify a port to be used. Defaults to 9118')
    parser.add_argument('-a', '--host', type=str, default='localhost', required=False,
                        help='Host address to listen on. Defaults to localhost')
    parser.add_argument('-c', '--collector', type=str, default='', required=False,
                        help='Condor collector address. Defaults to localhost')
    args = parser.parse_args()
    port = args.port
    address = args.host
    collector_address = args.collector

    try:
        from exporter.wsgi import wsgi_collector
        REGISTRY.unregister(wsgi_collector)
        REGISTRY.register(CondorCollector(collector_address))

        start_wsgi_server(addr=address, port=port)
        print("Exporter listening on %s:%d" % (address, port))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted, Shutting down")
        exit(0)


if __name__ == "__main__":
    main()
