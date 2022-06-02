import ipaddress
from socket import AF_INET, AF_INET6

import dbus
import netifaces

from pyroute2 import IPRoute

from systemd_resolved_docker.utils import get_interface_name


class SystemdResolvedConnector:
    def __init__(self, docker_interface, listen_addresses, dns_domains, cli):
        super().__init__()

        self.docker_interfaces = []
        self.listen_addresses = listen_addresses
        self.dns_domains = dns_domains
        self.cli = cli

        if docker_interface:
            self.register(docker_interface)
        else:
            for network in self.cli.networks.list():
                bridge_if_name = get_interface_name(network)
                if bridge_if_name:
                    self.register(bridge_if_name)

    @staticmethod
    def resolve_ifindex(docker_interface):
        with IPRoute() as ipr:
            ifi = ipr.link_lookup(ifname=docker_interface)
            if not ifi:
                raise ValueError("Unknown interface '%s'" % docker_interface)

            return ifi[0]

    @staticmethod
    def if_manager():
        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('org.freedesktop.resolve1', '/org/freedesktop/resolve1')
        return dbus.Interface(proxy, 'org.freedesktop.resolve1.Manager')

    def register(self, network_interface):
        """ Callback to be triggered from DockerWatcher upon creation of a network interface """
        if network_interface in self.docker_interfaces:
            return

        if self.listen_addresses:
            listen_addresses = self.listen_addresses
        else:
            listen_addresses = [netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']]

        domains = [[domain.strip("."), True] for domain in self.dns_domains]
        ips = [
            [
                AF_INET if isinstance(ip, ipaddress.IPv4Address) else AF_INET6,
                ip.packed
            ]
            for ip in [ipaddress.ip_address(ip) for ip in listen_addresses]
        ]
        if_index = self.resolve_ifindex(network_interface)

        manager = self.if_manager()
        manager.SetLinkDomains(if_index, domains)
        manager.SetLinkDNS(if_index, ips)
        manager.SetLinkDNSSEC(if_index, "no")

        print(f"Registered {network_interface}")

        self.docker_interfaces.append(network_interface)

    def unregister(self, network_interface):
        """ Callback to be triggered from DockerWatcher upon destruction of a network interface """
        if network_interface not in self.docker_interfaces:
            return
        try:
            if_index = self.resolve_ifindex(network_interface)
            manager = self.if_manager()
            manager.RevertLink(if_index)
        except ValueError:
            pass  # interface already down

        print(f"Unregistered {network_interface}")

        self.docker_interfaces = list(filter(lambda x: x != network_interface, self.docker_interfaces))

    def stop(self):
        interface_list_copy = self.docker_interfaces.copy()
        for n in interface_list_copy:
            self.unregister(n)
