from unittest import TestCase

from .utils import sanify_domain


class TestUtils(TestCase):
    def test_sanify_domain(self):
        self.assertEquals(".domain", sanify_domain(".domain"))
        self.assertEquals(".domain", sanify_domain("domain"))

        self.assertEquals(".domain", sanify_domain(" .domain "))
        self.assertEquals(".domain", sanify_domain(" domain "))
