from prometheus_client import REGISTRY, make_wsgi_app
from exporter.CondorExporter import CondorCollector



collector_address = "172.30.65.178"
REGISTRY.register(CondorCollector(collector_address))
application = make_wsgi_app()
