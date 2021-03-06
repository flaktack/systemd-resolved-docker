import docker

from threading import Thread


class DockerHost:
    def __init__(self, host_names, ip, interface=None):
        self.host_names = host_names
        self.ip = ip
        self.interface = interface


class DockerWatcher(Thread):
    """
        Thread based module for watching for docker container changes.
    """

    def __init__(self, handler, cli=None):
        super().__init__()

        if cli is None:
            cli = docker.from_env()

        self.daemon = True
        self.handler = handler
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

        for c in self.cli.containers.list():
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

        hostnames = [DockerHost(hosts, ip) for ip, hosts in domain_records.items()]

        self.handler.handle_hosts(hostnames)


if __name__ == '__main__':
    def callback(hosts):
        print("Received hosts:", len(hosts))
        for host in hosts:
            print("%s - %s" % (host.ip, ", ".join(host.host_names)))


    watcher = DockerWatcher(callback)
    watcher.start()
