import docker

from threading import Thread

from systemd_resolved_docker.utils import get_interface_name


class DockerHost:
    def __init__(self, host_names, ip, interface=None):
        self.host_names = host_names
        self.ip = ip
        self.interface = interface


class DockerWatcher(Thread):
    """
        Thread based module for watching for docker container changes.
    """

    def __init__(self, dns_connector, systemd_resolver, cli=None):
        super().__init__()

        if cli is None:
            cli = docker.from_env()

        self.daemon = True
        self.dns_connector = dns_connector
        self.cli = cli
        self.systemd_resolver = systemd_resolver

        self.collect_from_containers()

    def run(self) -> None:

        for e in self.cli.events(decode=True):
            status = e.get('status', False)
            if status in ('die', 'start'):
                self.collect_from_containers()
            elif e.get('Type') == 'network':
                network_id = e.get('Actor').get('ID')
                if e.get('Action') == 'destroy':
                    self.dns_connector.stop_dns(network_id)
                    self.systemd_resolver.unregister(f"br-{network_id[0:12]}")  # we don't expect "docker0" to shut down
                elif e.get('Action') == 'create':
                    self.dns_connector.start_dns(network_id)
                    self.systemd_resolver.register(f"br-{network_id[0:12]}")

        return

    def collect_from_containers(self):
        domain_records = {}

        compose_names = []
        duplicate_compose_names = []

        for c in self.cli.containers.list():
            if not c.attrs['State'].get('Running'):
                continue
            common_hostnames = []

            # container_id (.docker), only the first 12 characters need to be used
            container_id = c.attrs['Id']
            common_hostnames.append(container_id[0:12])

            # hostname (.docker), hostname.domainname (.docker)
            hostname = c.attrs['Config']['Hostname']
            domain = c.attrs['Config'].get('Domainname')

            # if no explicit --hostname is provided, than it will be the first 12 characters of the container_id.
            # In that case, the hostname can be ignored
            if hostname != container_id[:12]:
                if len(domain) > 0:
                    common_hostnames.append('%s.%s' % (hostname, domain))
                else:
                    common_hostnames.append(hostname)

            if c.attrs['Config'].get('Labels'):
                compose_name = c.attrs['Config']['Labels'].get('com.docker.compose.service')
            else:
                compose_name = None

            if compose_name:
                common_hostnames.append(compose_name)
                if compose_name in compose_names:
                    duplicate_compose_names.append(compose_name)
                else:
                    compose_names.append(compose_name)

            name = c.attrs['Name'][1:]
            settings = c.attrs['NetworkSettings']
            for netname, network in settings.get('Networks', {}).items():
                ip = network.get('IPAddress', False)
                if not ip or ip == "":
                    continue

                # record the container name DOT network
                # eg. container is named "foo", and network is "demo",
                #     so create "foo.demo" domain name
                # (avoiding default network named "bridge")
                record = domain_records.get(ip, [*common_hostnames])
                if netname != "bridge":
                    record.append('%s.%s' % (name, netname))

                domain_records[ip] = record

        for ip, hosts in domain_records.items():
            domain_records[ip] = list(filter(lambda h: h not in duplicate_compose_names, hosts))

        hostnames = [DockerHost(hosts, ip) for ip, hosts in domain_records.items()]

        self.dns_connector.handle_hosts(hostnames)


if __name__ == '__main__':
    def callback(hosts):
        print("Received hosts:", len(hosts))
        for host in hosts:
            print("%s - %s" % (host.ip, ", ".join(host.host_names)))


    watcher = DockerWatcher(callback)
    watcher.start()
