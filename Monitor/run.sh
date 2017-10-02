#! /bin/bash

function usage {
    echo "Usage: $0 run | start | restart | stop | delete ";
    exit 1;
    }

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

GRAFANA_PASS="secret"
GRAFANA_PORT="3000"
PROMETHEUS_PORT="9091"


function run {
    # run the docker containers
    ## Prometheus Server
    docker run -d -p $PROMETHEUS_PORT:9090 --name prom-server \
    -v $DIR/prometheus:/etc/prometheus \
    -v $DIR/storage:/prometheus \
    prom/prometheus -alertmanager.url=http://alertmanager:9093 \
    -config.file=/etc/prometheus/prometheus.yml \

    ## Grafana
    docker run -d -p 3000:3000 --name grafana \
    -e "GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_PASS" \
    --link prom-server:prom-server \
    grafana-monitor
    printf "Starting Grafana "
    until $(curl --output /dev/null --silent --fail http://127.0.0.1:3000); do
      printf "."
      sleep 5
    done
    printf "\n"
    add_datasource
    dashboards_arr=($DIR/grafana/dashboards/*)
    for f in "${dashboards_arr[@]}"; do
       add_dashboard $f
    done
}

function add_datasource {
  echo "Adding prometheus data source"
  curl --output /dev/null --silent\
  -H "Content-Type: application/json" -X POST \
  -d "{\"name\":\"Prometheus\",\"type\":\"prometheus\",\"access\":\"proxy\",\"url\":\"http://prom-server:9090\",\"basicAuth\":false}" \
  http://admin:$GRAFANA_PASS@127.0.0.1:3000/api/datasources
}
function add_dashboard () {
  echo "Adding dashboard from $1"
  echo "{\"dashboard\": `cat $1` , \
   \"inputs\": [{\"name\": \"DS_PROMETHEUS\", \
              \"pluginId\": \"prometheus\", \"type\": \"datasource\", \
              \"value\":\"Prometheus\"}], \
   \"overwrite\": true}" | curl --output /dev/null --silent \
  -H "Content-Type: application/json" -X POST \
  -d @- http://admin:$GRAFANA_PASS@127.0.0.1:3000/api/dashboards/import
}
#  echo "{\"dashboard\": `cat $1` }" | curl --output /dev/null --silent\

function build {

  cd $DIR/grafana/plugins
  tar xzf *tgz
  cd $DIR
  docker build -t grafana-monitor $DIR/grafana
}

function stop {
    #Stop the aplication
    docker stop prom-server grafana
}

function start {
    #start the aplication
    docker start prom-server grafana
}

function restart {
    #restart the aplication
    docker restart prom-server grafana
}

function delete {
    #Stop application and delete all data
    stop;
    docker rm -f prom-server grafana
}

case "$1" in
    run) run ;;
    start) start ;;
    restart) restart ;;
    stop) stop ;;
    delete) delete ;;
    build) build ;;
    *) usage ;;
esac
