#!/usr/bin/env python3

import os
import signal

import docker
from systemd import daemon

from .dockerdnsconnector import DockerDNSConnector
from .resolvedconnector import SystemdResolvedConnector
from .utils import find_default_docker_bridge_gateway, parse_ip_port, parse_listen_address, remove_dummy_interface, \
    create_dummy_interface, sanify_domain


class Handler:
    def on_start(self):
        daemon.notify('READY=1')
        self.log("Started daemon")

    def on_update(self, hosts):
        if len(hosts) > 0:
            message = "Refreshed - %d items\n\t%s" % (len(hosts), '\n\t'.join(map(lambda x: str(x), hosts)))
        else:
            message = "Refreshed - no running containers"

        self.log(message)

    def on_stop(self):
        self.log("Stopped daemon")

    def log(self, message):
        print(message)


def main():
    systemd_resolved_interface = os.environ.get("SYSTEMD_RESOLVED_INTERFACE", "srd-dummy")
    systemd_resolved_listen_address = os.environ.get("SYSTEMD_RESOLVED_LISTEN_ADDRESS", None)
    docker_listen_address = os.environ.get("DOCKER_LISTEN_ADDRESS", None)
    dns_server = parse_ip_port(os.environ.get("UPSTREAM_DNS_SERVER", "127.0.0.53"))
    default_domain = os.environ.get("DEFAULT_DOMAIN", "docker")
    default_host_ip = os.environ.get("DEFAULT_HOST_IP", "127.0.0.1")

    tld = os.environ.get('ALLOWED_DOMAINS', None)
    if tld is None or len(tld.strip()) == 0:
        domains = [".docker"]
    else:
        domains = [sanify_domain(item) for item in tld.split(',')]

    cli = docker.from_env()
    docker_gateway = find_default_docker_bridge_gateway(cli)

    handler = Handler()
    handler.log("Default domain: %s, allowed domains: %s" % (default_domain, ", ".join(domains)))

    systemd_resolved_listen_addresses = parse_listen_address(systemd_resolved_listen_address,
                                                             lambda: [parse_ip_port("127.0.0.153:53")])
    docker_listen_addresses = parse_listen_address(docker_listen_address,
                                                   lambda: [parse_ip_port(entry['gateway']) for entry in
                                                            docker_gateway])

    handler.log("Creating interface %s" % systemd_resolved_interface)
    remove_dummy_interface(systemd_resolved_interface)
    create_dummy_interface(systemd_resolved_interface, systemd_resolved_listen_addresses)

    resolved = SystemdResolvedConnector(systemd_resolved_interface, systemd_resolved_listen_addresses, domains, handler)

    dns_connector = DockerDNSConnector(systemd_resolved_listen_addresses + docker_listen_addresses, dns_server, domains,
                                       default_domain, default_host_ip, handler, cli)
    dns_connector.start()

    resolved.register()

    def sig_handler(signum, frame):
        handler.log("Stopping - %s" % signal.Signals(signum))
        resolved.unregister()
        dns_connector.stop()

        handler.log("Removing interface %s" % systemd_resolved_interface)
        remove_dummy_interface(systemd_resolved_interface)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    signal.pause()


if __name__ == '__main__':
    main()
