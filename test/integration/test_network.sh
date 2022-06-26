#!/usr/bin/env bash

. ./functions.sh

NETWORK1=testnet1-$TEST_PREFIX
NETWORK2=testnet2-$TEST_PREFIX

docker network create --label $TEST_LABEL $NETWORK1 > /dev/null
docker network create --label $TEST_LABEL $NETWORK2 > /dev/null

ALLOWED_DOMAINS=.docker,.$NETWORK1 start_systemd_resolved_docker

container1_id=$(docker_run network1 --network $NETWORK1)
container1_ip=$(docker_ip ${container1_id})
container1_name=$(docker_name ${container1_id})

container2_id=$(docker_run network2 --name name2 --network $NETWORK1)
container2_ip=$(docker_ip ${container2_id})
container2_name=$(docker_name ${container2_id})

container3_id=$(docker_run network3 --network $NETWORK2)
container3_ip=$(docker_ip ${container3_id})
container3_name=$(docker_name ${container3_id})

container4_id=$(docker_run network4 --name name4 --network $NETWORK2)
container4_ip=$(docker_ip ${container4_id})
container4_name=$(docker_name ${container4_id})

query_ok   $container1_name.$NETWORK1        $container1_ip
query_fail $container1_name.$NETWORK1.docker $container1_ip

query_ok   $container2_name.$NETWORK1        $container2_ip
query_ok              name2.$NETWORK1        $container2_ip
query_fail $container2_name.$NETWORK1.docker $container2_ip

query_ok   $container3_name.$NETWORK2.docker $container3_ip
query_fail $container3_name.$NETWORK2        $container3_ip

query_ok   $container4_name.$NETWORK2.docker $container4_ip
query_ok              name4.$NETWORK2.docker $container4_ip
query_fail $container4_name.$NETWORK2        $container4_ip
