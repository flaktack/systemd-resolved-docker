import dnslib.server
import socket


class UDPServer4(dnslib.server.UDPServer):
    address_family = socket.AF_INET


class UDPServer6(dnslib.server.UDPServer):
    address_family = socket.AF_INET6
