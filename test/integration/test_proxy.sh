#!/usr/bin/env bash

. ./functions.sh

start_systemd_resolved_docker

NETWORK=testnet1-$TEST_PREFIX
docker network create --label $TEST_LABEL $NETWORK > /dev/null

container_id=$(docker_run resolvetest1 --hostname resolvetest1)
container_ip=$(docker_ip ${container_id})

dns_ip=$(docker network inspect bridge --format '{{ range .IPAM.Config }}{{ .Gateway }}{{ end }}')

query_ok   resolvetest1.docker $container_ip

# Case 1: generated domains are resolved in containers on the default network
#         The DNS server is provided explicitly, since it was not provided to the daemon
docker run --dns $dns_ip       --rm alpine sh -c "apk add bind-tools && host resolvetest1.docker"

# Case 2: generated domains are resolved in containers on other networks
docker run  --network $NETWORK --rm alpine sh -c "apk add bind-tools && host resolvetest1.docker"
