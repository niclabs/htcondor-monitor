from prometheus_client import REGISTRY, make_wsgi_app
from exporter.CondorExporter import CondorCollector
from exporter.Config import Config


collector_address = Config.COLLECTOR_ADDRESS
REGISTRY.register(CondorCollector(collector_address))
application = make_wsgi_app()
