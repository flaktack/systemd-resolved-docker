
# Test run for multiple bridge creation and teardown

Here are just some sample docker-compose files to play around with docker network and multiple bridges

    docker-compose -f sample/docker-compose.yml up -d
    ping -c1 sample_broker_1.sample_pytest.docker

    docker-compose -f sample_no_gateway/docker-compose.yml up -d
    ping -c1 sample_no_gateway_broker_1.sample_no_gateway_pytest_nogw.docker
    
    docker-compose -f sample_no_gateway/docker-compose.yml stop
    docker-compose -f sample/docker-compose.yml stop

    docker-compose -f sample_no_gateway/docker-compose.yml rm -f
    docker-compose -f sample/docker-compose.yml rm -f

    docker network prune -f
