import threading
from typing import List

from dnslib import A, CLASS, DNSLabel, QTYPE, RR
from dnslib.proxy import ProxyResolver
from dnslib.server import DNSServer

from .dockerwatcher import DockerWatcher, DockerHost
from .interceptresolver import InterceptResolver
from .utils import IpAndPort
from .zoneresolver import ZoneResolver


class DockerDNSConnector:
    def __init__(self, listen_addresses: List[IpAndPort], upstream_dns_server: IpAndPort, dns_domains, default_domain,
                 default_host_ip, handler, cli):
        super().__init__()

        self.default_domain = default_domain
        self.handler = handler

        self.dns_domains_globs = ['*%s' % domain if domain.startswith('.') else domain for domain in dns_domains]

        self.resolver = ZoneResolver([], glob=True)
        self.servers = []

        resolver = InterceptResolver(self.dns_domains_globs, self.resolver,
                                     ProxyResolver(upstream_dns_server.ip.exploded, port=upstream_dns_server.port,
                                                   timeout=5))
        self.handler.log("Unhandled DNS requests will be resolved using %s" % upstream_dns_server)
        self.handler.log("DNS server listening on %s" % ", ".join(map(lambda x: str(x), listen_addresses)))

        for ip_and_port in listen_addresses:
            server = DNSServer(resolver, address=ip_and_port.ip.exploded, port=ip_and_port.port)
            server.thread_name = "%s:%s" % (ip_and_port.ip, ip_and_port.port)
            self.servers.append(server)

        self.watcher = DockerWatcher(self, default_host_ip, cli)

    def start(self):
        self.watcher.start()

        for server in self.servers:
            server.thread = threading.Thread(target=server.server.serve_forever, name=server.thread_name)
            server.thread.start()

        self.handler.on_start()

    def stop(self):
        for server in self.servers:
            server.stop()

        for server in self.servers:
            server.thread.join()

        self.handler.on_stop()

    def handle_hosts(self, hosts):
        zone = []
        host_names = []
        mapped_hosts = []

        for host in hosts:
            mh = DockerHost([], host.ip)
            mapped_hosts.append(mh)

            for host_name in host.host_names:
                hn = self.as_allowed_hostname(host_name)
                mh.host_names.append(hn)

                rr = RR(hn, QTYPE.A, CLASS.IN, 1, A(host.ip))
                zone.append(rr)
                host_names.append(hn)

        self.resolver.update(zone)

        self.handler.on_update(mapped_hosts)

    def as_allowed_hostname(self, hostname):
        for domain in self.dns_domains_globs:
            if DNSLabel(hostname).matchGlob(domain):
                return hostname

        return "%s.%s" % (hostname, self.default_domain)
