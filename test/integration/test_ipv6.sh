#!/usr/bin/env bash

. ./functions.sh

exec 10<<EOF
version: "2.1"
services:
  webserver:
    image: nginx
    labels:
     - $TEST_LABEL
    networks:
      - network
  broker:
    image: redis
    labels:
     - $TEST_LABEL
    networks:
      - network

networks:
  network:
    driver: bridge
    enable_ipv6: true
    labels:
     - $TEST_LABEL
    ipam:
      driver: default
      config:
        - subnet: 2001:db8:a::/64
          gateway: 2001:db8:a::1
EOF

exec 20<<EOF
version: "2.1"
services:
  broker:
    image: redis
    labels:
     - $TEST_LABEL
    networks:
      - network

networks:
  network:
    driver: bridge
    enable_ipv6: true
    labels:
     - $TEST_LABEL
    ipam:
      driver: default
      config:
        - subnet: 2001:db8:b::/64
          gateway: 2001:db8:b::1
EOF

ALLOWED_DOMAINS=.docker,.$TEST_PREFIX start_systemd_resolved_docker

docker-compose --file /dev/fd/10 --project-name $TEST_PREFIX up --detach --scale webserver=2

broker1_ip=$(docker_ipv6 ${TEST_PREFIX}_broker_1)
webserver1_ip=$(docker_ipv6 ${TEST_PREFIX}_webserver_1)
webserver2_ip=$(docker_ipv6 ${TEST_PREFIX}_webserver_2)

query_ok     broker.$TEST_PREFIX $broker1_ip
query_ok   1.broker.$TEST_PREFIX $broker1_ip

query_ok     webserver.$TEST_PREFIX $webserver1_ip
query_ok     webserver.$TEST_PREFIX $webserver2_ip
query_ok   1.webserver.$TEST_PREFIX $webserver1_ip
query_ok   2.webserver.$TEST_PREFIX $webserver2_ip

query_ok     broker.docker $broker1_ip

docker-compose --file /dev/fd/20 --project-name ${TEST_PREFIX}_2 up --detach
query_fail   broker.docker
