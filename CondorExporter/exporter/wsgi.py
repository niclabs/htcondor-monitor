from prometheus_client import REGISTRY, make_wsgi_app
from exporter.CondorExporter import CondorCollector
from exporter.Config import Config

application = make_wsgi_app()
collector_address = Config.COLLECTOR_ADDRESS
wsgi_collector = CondorCollector(collector_address)
REGISTRY.register(wsgi_collector)
