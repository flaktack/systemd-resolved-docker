#!/usr/bin/env python3

import os
import docker
import signal
from systemd import daemon, journal

from systemd_resolved_docker.resolvedconnector import SystemdResolvedConnector
from .dockerdnsconnector import DockerDNSConnector
from .utils import find_default_docker_bridge_gateways, find_docker_dns_servers


class Handler:
    def on_start(self):
        daemon.notify('READY=1')
        self.log("Started daemon")

    def on_update(self, hosts):
        message = "Refreshed - %d items (%s)" % (
            len(hosts), ' '.join(["%s/%s" % (host.ip, ','.join(host.host_names)) for host in hosts]))

        self.log(message)

    def on_stop(self):
        self.log("Stopped daemon")

    def log(self, message):
        print(message)


def main():
    dns_server = os.environ.get("DNS_SERVER", "127.0.0.53")
    default_domain = os.environ.get("DEFAULT_DOMAIN", "docker")
    listen_port = int(os.environ.get("LISTEN_PORT", "53"))
    listen_address = os.environ.get("LISTEN_ADDRESS", None)

    tld = os.environ.get('ALLOWED_DOMAINS', None)
    if tld is None or len(tld.strip()) == 0:
        domains = [".docker"]
    else:
        domains = [item.strip() for item in tld.split(',')]

    cli = docker.from_env()
    docker_dns_servers = find_docker_dns_servers(cli)
    docker_gateway = find_default_docker_bridge_gateways(cli)

    if listen_address is None or len(listen_address) < 1:
        listen_addresses = []
        for entry in docker_gateway:
            if 'gateway' in entry:
                listen_addresses.append(entry['gateway'])
    else:
        listen_addresses = listen_address.split(",")

    interface = os.environ.get('DOCKER_INTERFACE', None)
    if interface is None or len(interface) < 1:
        interfaces = []
        for gateway in docker_gateway:
            if gateway['interface'] not in interfaces:
                interfaces.append(gateway['interface'])
    else:
        interfaces = [interface]

    handler = Handler()
    handler.log("Default domain: %s, allowed domains: %s" % (default_domain, ", ".join(domains)))

    resolves = []
    for interface in interfaces:
        handler.log(f"Adding interface {interface}")
        resolves.append(SystemdResolvedConnector(interface, listen_addresses, domains))

    dns_connector = DockerDNSConnector(listen_addresses, listen_port, dns_server, domains, default_domain, interfaces,
                                       handler, cli)
    dns_connector.start()

    for resolver in resolves:
        resolver.register()

    def sig_handler(signum, frame):
        handler.log("Stopping - %s" % signal.Signals(signum))
        for resolver in resolves:
            resolver.unregister()
        dns_connector.stop()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    signal.pause()


if __name__ == '__main__':
    main()
