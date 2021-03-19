import codecs, os.path
from setuptools import setup, find_packages


# use README.md as readme
def readme():
    with open('README.md') as f:
        return f.read()
 

# get __version__ from a file
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()
 

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name='systemd-resolved-docker',
    url='https://github.com/flaktack/systemd-resolved-docker',
    license='MIT',
    author='Zsombor Welker',
    author_email='flaktack@flaktack.net',
    install_requires=["docker", "dnslib", "systemd-python", "dbus-python", "pyroute2"],
    description='systemd-resolved and docker DNS integration',
    long_description=readme(),
    long_description_content_type="text/markdown",
    package_dir={
      '': 'src',
    },
    packages=find_packages('src'),
    entry_points={
        'console_scripts': [
            'systemd-resolved-docker=systemd_resolved_docker.cli:main',
        ],
    },
    excluded=['rpms/*'],

    # extract version from source
    version=get_version("src/systemd_resolved_docker/__init__.py"),
)
