from setuptools import setup, Extension
import subprocess

def pkg_config(packages):
    def get_output(option):
        return subprocess.check_output(
            ['pkg-config', option] + packages
        ).decode('utf-8').strip().split()
    return get_output('--cflags'), get_output('--libs')


cflags, libs = pkg_config(['libavcodec', 'libavformat', 'libavfilter'])
djmodule = Extension('dj', sources=['djmodule.c'], extra_compile_args=cflags, extra_link_args=libs)

setup(
    name='dj',
    version='1.0',
    description='DJ EBAN',
    ext_modules=[djmodule],
)
