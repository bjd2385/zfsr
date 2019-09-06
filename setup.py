"""
Set up zfsretention for install.
"""

from setuptools import setup, find_packages


setup(
    name='zfsr',
    version='1.0',
    description='Python-based tool for managing ZFS pool snapshots and replication',
    author='Brandon Doyle',
    author_email='bjd2385@aperiodicity.com',
    license='MIT',
    keywords='zfs',
    packages=find_packages(),
    install_requires=[
        'weir==0.4.0',
        'superprocess<0.3.*,>=0.2.0'
    ]
)
