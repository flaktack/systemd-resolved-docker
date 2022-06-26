#!/usr/bin/env bash

. ./functions.sh

container1_id=$(docker_run id1)
container1_ip=$(docker_ip ${container1_id})
container2_id=$(docker_run id2)
container2_ip=$(docker_ip ${container2_id})


DEFAULT_DOMAIN=dockerx ALLOWED_DOMAINS=.dockerx start_systemd_resolved_docker
query_ok ${container1_id}.dockerx $container1_ip
query_ok ${container2_id}.dockerx $container2_ip

query_fail ${container1_id}.docker
query_fail ${container2_id}.docker


DEFAULT_DOMAIN=test123 ALLOWED_DOMAINS=.docker start_systemd_resolved_docker
query_ok ${container1_id}.test123 $container1_ip
query_ok ${container2_id}.test123 $container2_ip

query_fail ${container1_id}.docker
query_fail ${container2_id}.docker
