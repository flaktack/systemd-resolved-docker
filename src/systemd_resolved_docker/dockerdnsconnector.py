import ipaddress
import threading
from socket import AF_INET, AF_INET6

import dbus
from dnslib import A, CLASS, DNSLabel, QTYPE, RR
from dnslib.proxy import ProxyResolver
from dnslib.server import DNSServer
from pyroute2 import IPRoute

from .dockerwatcher import DockerWatcher, DockerHost
from .interceptresolver import InterceptResolver
from .zoneresolver import ZoneResolver


class DockerDNSConnector:
    def __init__(self, listen_addresses, listen_port, upstream_dns_server, dns_domains, default_domain,
                 docker_interface, handler, cli):
        super().__init__()

        self.listen_addresses = listen_addresses
        self.upstream_dns_server = upstream_dns_server
        self.default_domain = default_domain
        self.dns_domains = dns_domains
        self.docker_interface = docker_interface
        self.handler = handler

        self.dns_domains_globs = ['*%s' % domain if domain.startswith('.') else domain for domain in dns_domains]

        self.resolver = ZoneResolver([])
        self.servers = []

        resolver = InterceptResolver(self.dns_domains_globs, self.resolver,
                                     ProxyResolver(upstream_dns_server, port=53, timeout=5))
        self.handler.log("Unhandled DNS requests will be resolved using %s:53" % upstream_dns_server)

        for address in listen_addresses:
            server = DNSServer(resolver, address=address, port=listen_port)
            self.servers.append(server)
            self.handler.log("DNS server listening on %s:%s" % (address, listen_port))

        self.watcher = DockerWatcher(self, cli)

    def start(self):
        self.watcher.start()

        for server in self.servers:
            server.thread = threading.Thread(target=server.server.serve_forever)
            server.thread.start()

        self.handler.on_start()

    def stop(self):
        self.update_resolved(enabled=False)

        for server in self.servers:
            server.stop()

        for server in self.servers:
            server.thread.join()

        self.handler.on_stop()

    def update_resolved(self, enabled=True):
        with IPRoute() as ipr:
            ifi = ipr.link_lookup(ifname=self.docker_interface)
            if not ifi:
                raise ValueError("Unknown interface '%s'" % self.docker_interface)

            ifindex = ifi[0]

            system_bus = dbus.SystemBus()
            proxy = system_bus.get_object('org.freedesktop.resolve1', '/org/freedesktop/resolve1')
            manager = dbus.Interface(proxy, 'org.freedesktop.resolve1.Manager')

            if enabled:
                domains = [[domain.strip("."), True] for domain in self.dns_domains]
                ips = [
                    [
                        AF_INET if isinstance(ip, ipaddress.IPv4Address) else AF_INET6,
                        ip.packed
                    ]
                    for ip in [ipaddress.ip_address(ip) for ip in self.listen_addresses]
                ]

                manager.SetLinkDomains(ifindex, domains)
                manager.SetLinkDNS(ifindex, ips)
            else:
                manager.RevertLink(ifindex)

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
        self.update_resolved(enabled=len(host_names) > 0)

        self.handler.on_update(mapped_hosts)

    def as_allowed_hostname(self, hostname):
        for domain in self.dns_domains_globs:
            if DNSLabel(hostname).matchGlob(domain):
                return hostname

        return "%s.%s" % (hostname, self.default_domain)
