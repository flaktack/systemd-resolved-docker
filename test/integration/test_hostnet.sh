#!/usr/bin/env bash

. ./functions.sh

container_id=$(docker_run hostnet1 --network host --hostname hostnet1)

start_systemd_resolved_docker

query_ok   $container_id.docker 127.0.0.1
query_ok        hostnet1.docker 127.0.0.1
query_ok   ${TEST_PREFIX}-hostnet1.host.docker 127.0.0.1

DEFAULT_HOST_IP=1.2.3.4 start_systemd_resolved_docker

query_ok   $container_id.docker 1.2.3.4
query_ok        hostnet1.docker 1.2.3.4
query_ok   ${TEST_PREFIX}-hostnet1.host.docker 1.2.3.4
