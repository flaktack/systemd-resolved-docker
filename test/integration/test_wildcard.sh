#!/usr/bin/env bash

. ./functions.sh

ALLOWED_DOMAINS=.docker,.$TEST_PREFIX start_systemd_resolved_docker

container_id=$(docker_run wildcard1 --hostname "*.$TEST_PREFIX")
container_ip=$(docker_ip ${container_id})

query_ok   anything.$TEST_PREFIX $container_ip
query_ok otherthing.$TEST_PREFIX $container_ip
