from dnslib.server import BaseResolver


class InterceptResolver(BaseResolver):
    """
        Simple resolver that tries to handle queries local, and if that is unhandled the forwards the requests to
        a fallback resolver.
    """

    def __init__(self, local_domains, local_resolver, fallback_resolver):
        self.local_domains = local_domains
        self.local_resolver = local_resolver
        self.fallback_resolver = fallback_resolver

    def resolve(self, request, handler):
        if self.is_local(request.q.qname):
            return self.local_resolver.resolve(request, handler)
        else:
            return self.fallback_resolver.resolve(request, handler)

    def is_local(self, qname):
        for domain in self.local_domains:
            if qname.matchGlob(domain):
                return True
        return False
