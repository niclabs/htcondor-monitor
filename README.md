# htcondor-monitor
Monitoring tool for htcondor, includes a Python exporter to expose metrics and Prometheus and Grafana containers for collection and visualization.

## Exporter

The importer is implemented in Python using the [prometheus_client](https://github.com/prometheus/client_python) and [htcondor](https://htcondor-python.readthedocs.io/en/latest/) libraries.

It can be run by executing the `CondorExporter.py` script or with uWSGI using the `wsgi.py` script.

## Monitor
The sample monitor included in this repository uses docker containers to deploy Prometheus and Grafana servers to collect and display the metrics exposed by the exporter.

Visit our project [wiki](https://github.com/niclabs/htcondor-monitor/wiki) for more detailed instructions on how to run or modify any of the components.
