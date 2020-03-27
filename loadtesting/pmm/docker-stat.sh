#!/bin/bash
while "true"
do
    DOCKER_HOST=unix:///opt/scalr-server/run/dkr/docker.sock /opt/scalr-server/embedded/bin/docker ps -a | sed -n '1!p'| /usr/bin/wc -l | sed -ne 's/^/node_docker_containers_total /p' > /usr/local/percona/pmm-client/textfile-collector/docker_all.prom;
    DOCKER_HOST=unix:///opt/scalr-server/run/dkr/docker.sock /opt/scalr-server/embedded/bin/docker ps | sed -n '1!p'| /usr/bin/wc -l | sed -ne 's/^/node_docker_containers_running_total /p' >/usr/local/percona/pmm-client/textfile-collector/docker_running.prom;
    sleep 10
done
