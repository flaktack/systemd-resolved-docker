#!/usr/bin/env bash

. ./functions.sh

ALLOWED_DOMAINS=.docker,host2,.domain2 start_systemd_resolved_docker

test_query hostname1 host1.docker --hostname host1
query_fail host1

test_query hostname2 host2.docker --hostname host2
query_fail host2

test_query hostdomain1 host1.domain1.docker --hostname host1 --domainname domain1
query_fail host1.domain1

test_query hostdomain2 host2.domain2        --hostname host2 --domainname domain2
query_fail host2.domain2.docker