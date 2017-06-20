from setuptools import find_packages, setup, Extension
import os
from sys import platform
from setuptools.command.install import install
from distutils.command.build import build
from subprocess import call
from multiprocessing import cpu_count

BASEPATH = os.path.dirname(os.path.abspath(__file__))

class ESSPBuild(build):
    def run(self):
        # run original build code
        build.run(self)

        cmd = [
            'make',
        ]

        def compile():
            call(cmd, cwd=os.path.join(BASEPATH, "_eSSP"))

        self.execute(compile, [], 'Compiling library')

        if not self.dry_run:
            self.copy_file(os.path.join(BASEPATH, "_eSSP", "libessp.so"),
                           os.path.join(self.build_lib, "eSSP"))


class ESSPInstall(install):
    def initialize_options(self):
        install.initialize_options(self)
        self.build_scripts = None

    def finalize_options(self):
        install.finalize_options(self)
        self.set_undefined_options('build', ('build_scripts', 'build_scripts'))

    def run(self):
        # run original install code
        install.run(self)

        # install library
        self.copy_tree(self.build_lib, self.install_lib)


setup(name="eSSP6",
        version="1.0.5",
        description="Encrypted Smiley Secure Protocol Python 3 Implementation",
	long_description="Description is avaible in the github repository",
        author="Loan & Innovative Technology (Some of the C code)",
        author_email="minege@protonmail.com",
        platforms=["cygwin","osx"],
        license="MIT",
        url="https://github.com/Minege/eSSP",
        packages=find_packages(),
        cmdclass={
        'build': ESSPBuild,
        'install': ESSPInstall,
        },
        install_requires=[
        "",
        ]
        )
