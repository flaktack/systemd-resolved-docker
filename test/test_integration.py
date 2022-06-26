import os
import pathlib
import subprocess
import unittest

INTEGRATION_DIRECTORY = pathlib.Path(__file__).parent.resolve().joinpath("integration").as_posix()


def generate_test(name):
    def test(self):
        try:
            subprocess.check_output(
                ['bash', '-c', 'cd {} && ./{}'.format(INTEGRATION_DIRECTORY, name)], stderr=subprocess.STDOUT,
                text=True)
        except subprocess.CalledProcessError as ex:
            self.fail(ex.output)

    return test


def extend_testcase(cls):
    for file in os.listdir(INTEGRATION_DIRECTORY):
        if file.startswith("test") and file.endswith(".sh"):
            name = file.removesuffix(".sh")
            test = generate_test(file)
            setattr(cls, name, test)


class IntegrationTest(unittest.TestCase):
    pass


extend_testcase(IntegrationTest)

if __name__ == '__main__':
    unittest.main()
