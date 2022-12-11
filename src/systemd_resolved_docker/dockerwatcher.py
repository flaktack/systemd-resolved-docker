import ipaddress
from typing import List, Union

import docker

from threading import Thread


class DockerHost:
    def __init__(self, host_names: List[str], ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address], interface=None):
        self.host_names = host_names
        self.ip = ip
        self.interface = interface

    def __str__(self):
        return "%s/%s" % (self.ip, ','.join(self.host_names))


class DockerWatcher(Thread):
    """
        Thread based module for watching for docker container changes.
    """

    def __init__(self, handler, default_host_ip='127.0.0.1', cli=None):
        super().__init__()

        if cli is None:
            cli = docker.from_env()

        self.daemon = True
        self.handler = handler
        self.default_host_ip = default_host_ip
        self.cli = cli

    def run(self) -> None:
        self.collect_from_containers()

        for e in self.cli.events(decode=True):
            status = e.get('status', False)
            if status in ('die', 'start'):
                self.collect_from_containers()

        return

    def collect_from_containers(self):
        domain_records = {}

        non_unique_hostnames = set()
        duplicate_hostnames = set()

        for c in self.cli.containers.list():
            common_hostnames = []

            # container_id (.docker), only the first 12 characters need to be used
            container_id = c.attrs['Id']
            common_hostnames.append(container_id[0:12])

            # hostname (.docker), hostname.domainname (.docker)
            hostname = c.attrs['Config']['Hostname']
            domain = c.attrs['Config'].get('Domainname')

            # if no explicit --hostname is provided, then it will be the first 12 characters of the container_id.
            # In that case, the hostname can be ignored
            if hostname != container_id[:12]:
                if len(domain) > 0:
                    common_hostnames.append('%s.%s' % (hostname, domain))
                else:
                    common_hostnames.append(hostname)

            # for docker-compose services service.project (.docker) names are created
            if c.attrs['Config'].get('Labels') and c.attrs['Config']['Labels'].get('com.docker.compose.service') and \
                    c.attrs['Config']['Labels'].get('com.docker.compose.project'):
                compose_service = c.attrs['Config']['Labels'].get('com.docker.compose.service')
                compose_project = c.attrs['Config']['Labels'].get('com.docker.compose.project')

                common_hostnames.append(compose_service)
                common_hostnames.append("%s.%s" % (compose_service, compose_project))

                if compose_service in non_unique_hostnames:
                    duplicate_hostnames.add(compose_service)
                else:
                    non_unique_hostnames.add(compose_service)

                compose_container_number = c.attrs['Config']['Labels'].get('com.docker.compose.container-number')
                if compose_container_number:
                    common_hostnames.append("%s.%s.%s" % (compose_container_number, compose_service, compose_project))

            name = c.attrs['Name'][1:]
            settings = c.attrs['NetworkSettings']
            for netname, network in settings.get('Networks', {}).items():
                ips = [network[field] for field in ['IPAddress', 'GlobalIPv6Address'] if
                       field in network and network[field] != ""]
                if not ips:
                    if netname == 'host':
                        ips = [self.default_host_ip]
                    else:
                        continue

                # record the container name DOT network
                # eg. container is named "foo", and network is "demo",
                #     so create "foo.demo" domain name
                # (avoiding default network named "bridge")
                for ip in ips:
                    ipr = ipaddress.ip_address(ip)
                    record = domain_records.get(ipr, [*common_hostnames])
                    if netname != "bridge":
                        record.append('%s.%s' % (name, netname))

                    domain_records[ipr] = record

        for ip, hosts in domain_records.items():
            domain_records[ip] = list(filter(lambda h: h not in duplicate_hostnames, hosts))

        hostnames = [DockerHost(hosts, ip) for ip, hosts in domain_records.items()]

        self.handler.handle_hosts(hostnames)


if __name__ == '__main__':
    def callback(hosts):
        print("Received hosts:", len(hosts))
        for host in hosts:
            print("%s - %s" % (host.ip, ", ".join(host.host_names)))


    watcher = DockerWatcher(callback)
    watcher.start()
