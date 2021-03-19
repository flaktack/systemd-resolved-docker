import docker

from threading import Thread

from dnslib import DNSLabel


class DockerHost:
    def __init__(self, host_names, ip, interface=None):
        self.host_names = host_names
        self.ip = ip
        self.interface = interface


class DockerWatcher(Thread):
    """
        Thread based module for wathing for docker container changes.
    """

    def __init__(self, handler, domain_globs=None, default_domain=None, cli=None):
        super().__init__()

        if cli is None:
            cli = docker.from_env()

        if domain_globs is None:
            domain_globs = ["*.docker"]

        if default_domain is None:
            default_domain = ".docker"

        self.daemon = True
        self.handler = handler
        self.domain_globs = domain_globs
        self.default_domain = default_domain
        self.cli = cli

    def run(self) -> None:
        self.collect_from_containers()

        for e in self.cli.events(decode=True):
            status = e.get('status', False)
            if status in ('die', 'start'):
                self.collect_from_containers()

        return

    def collect_from_containers(self):
        hostnames = []

        domain_records = {}

        for c in self.cli.containers.list():
            # the records

            hostname = c.attrs['Config']['Hostname']
            domain = c.attrs['Config'].get('Domainname')

            if len(domain) > 0:
                hostname = '%s.%s' % (hostname, domain)

            if '.' not in hostname:
                hostname += self.default_domain

            # get container name
            name = c.attrs['Name'][1:]

            # now read network settings
            settings = c.attrs['NetworkSettings']
            for netname, network in settings.get('Networks', {}).items():
                ip = network.get('IPAddress', False)
                if not ip or ip == "":
                    continue

                record = domain_records.get(ip, [])
                # record the container name DOT network
                # eg. container is named "foo", and network is "demo",
                #     so create "foo.demo" domain name
                # (avoiding default network named "bridge")
                if netname != "bridge":
                    record.append('.%s.%s' % (name, netname))

                # check if the hostname is allowed
                for domain in self.domain_globs:
                    if DNSLabel(hostname).matchGlob(domain):
                        record.append(hostname)

                # do not append record if it's empty
                if len(record) > 0:
                    domain_records[ip] = record

        for ip, hosts in domain_records.items():
            hostnames.append(DockerHost(hosts, ip))

        self.handler.handle_hosts(hostnames)


if __name__ == '__main__':
    def callback(hosts):
        print("Received hosts:", len(hosts))
        for host in hosts:
            print("%s - %s" % (host.ip, ", ".join(host.host_names)))


    watcher = DockerWatcher(callback)
    watcher.start()
