set -e

TEST_PREFIX="$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 10)"
TEST_LABEL="systemd-resolved-docker=test-${TEST_PREFIX}"

trap "cleanup" EXIT

cleanup() {
  stop_systemd_resolved_docker
  docker ps --all   --filter label=${TEST_LABEL} --format '{{ .ID }}' | xargs --no-run-if-empty docker rm --force > /dev/null
  docker network ls --filter label=${TEST_LABEL} --format '{{ .ID }}' | xargs --no-run-if-empty docker network rm > /dev/null
}

start_systemd_resolved_docker() {
  stop_systemd_resolved_docker

  PYTHONPATH="$PWD/../../src:$PYTHONPATH" python -m systemd_resolved_docker.cli &
  SYSTEMD_RESOLVED_DOCKER_PID=$!

  sleep 2
}

stop_systemd_resolved_docker() {
  if [ ! -z "$SYSTEMD_RESOLVED_DOCKER_PID" ];
  then
    kill $SYSTEMD_RESOLVED_DOCKER_PID || true
    sleep 1

    SYSTEMD_RESOLVED_DOCKER_PID=""
  fi
}

docker_run() {
  local name=$1
  shift;

  docker run --detach --label "${TEST_LABEL}" --name "${TEST_PREFIX}-$name" --interactive $@ alpine | cut -c -12
}

docker_ip() {
  local container_id=$1
  shift;

  docker inspect --format '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container_id
}

docker_ipv6() {
  local container_id=$1
  shift;

  docker inspect --format '{{range.NetworkSettings.Networks}}{{.GlobalIPv6Address}}{{end}}' $container_id
}

docker_name() {
  local container_id=$1
  shift;

  docker inspect --format '{{ .Name }}' $container_id | cut -c2-
}

query_ok() {
  local query=$1
  local ip=$2
  shift; shift;

  if resolvectl query $query | grep $ip;
  then
    true
  else
    >&2 echo "Failed to resolve $query to $ip"
    false
  fi
}

query_fail() {
  local query=$1
  shift;

  if resolvectl query $query;
  then
    >&2 echo "Failing, resolved $query"
    false
  else
    true
  fi
}

test_query() {
  local name=$1
  local query=$2
  shift; shift;

  local id=$(docker_run $name $@)
  local ip=$(docker_ip $id)

  query_ok $query $ip
}
