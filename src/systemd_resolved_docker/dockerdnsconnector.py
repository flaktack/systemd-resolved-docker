import threading

from dnslib import A, CLASS, DNSLabel, QTYPE, RR
from dnslib.proxy import ProxyResolver
from dnslib.server import DNSServer
import netifaces

from .dockerwatcher import DockerWatcher, DockerHost
from .interceptresolver import InterceptResolver
from .utils import get_interface_name
from .zoneresolver import ZoneResolver


class DockerDNSConnector:
    """DockerDNSConnector

    Creates DNS servers for all docker bridges on the fly as needed.
    """

    def __init__(self, listen_addresses, listen_port, upstream_dns_server, dns_domains, default_domain,
                 handler, cli):
        super().__init__()

        self.listen_addresses = listen_addresses
        self.upstream_dns_server = upstream_dns_server
        self.default_domain = default_domain
        self.dns_domains = dns_domains
        self.handler = handler
        self.cli = cli
        self.listen_port = listen_port

        self.dns_domains_globs = ['*%s' % domain if domain.startswith('.') else domain for domain in dns_domains]

        self.resolver = ZoneResolver([])
        self.servers = {}

        self.iresolver = InterceptResolver(self.dns_domains_globs, self.resolver,
                                     ProxyResolver(upstream_dns_server, port=53, timeout=5))
        self.handler.log("Unhandled DNS requests will be resolved using %s:53" % upstream_dns_server)

        if listen_addresses:
            for address in listen_addresses:
                server = DNSServer(self.iresolver, address=address['gateway'], port=self.listen_port)
                server.thread_name = "%s:%s" % (address['gateway'], self.listen_port)
                self.servers[address['id']] = server
                self.handler.log("DNS server listening on %s:%s" % (address, self.listen_port))
        else:
            for network in self.cli.networks.list():
                if network.attrs['Driver'] == 'bridge':
                    self.start_dns(network.id)
        self.handler.on_start()

    def stop_dns(self, network_id):
        """ Callback to be triggered from DockerWatcher upon removal of a network interface """
        self.servers[network_id].stop()
        self.servers[network_id].thread.join()
        del self.servers[network_id]

    def start_dns(self, network_id):
        """ Callback to be triggered from DockerWatcher upon creation of a network interface """
        networks = self.cli.networks

        bridge_if_name = get_interface_name(networks.get(network_id))

        try:
            listen_ip = netifaces.ifaddresses(bridge_if_name)[netifaces.AF_INET][0]['addr']
        except BaseException as e:
            print(e)
            print(f"WARNING: Could not find a valid bind-address for a DNS server of interface {network_id}")
            return

        server = DNSServer(self.iresolver, address=listen_ip, port=self.listen_port)
        server.thread_name = "%s:%s" % (listen_ip, self.listen_port)
        self.servers[network_id] = server
        self.handler.log("DNS server listening on %s:%s" % (listen_ip, self.listen_port))

        self.servers[network_id].thread = threading.Thread(target=self.servers[network_id].server.serve_forever,
                                                           name=self.servers[network_id].thread_name)

        self.servers[network_id].thread.start()

    def stop(self):
        for server in self.servers:
            self.servers[server].stop()

        for server in self.servers:
            self.servers[server].thread.join()

        self.handler.on_stop()

    def handle_hosts(self, hosts):
        """ Callback to be triggered from DockerWatcher upon changes in hosts
        """
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
