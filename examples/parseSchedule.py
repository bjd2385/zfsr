#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parse the schedule / YAML file.
"""

import yaml


def getAsDictYAML(fName: str) -> None:
    """
    Parse YAML and return it as a Python dict.
    """
    with open('exampleRetention.yaml', 'r') as y:
        for pool in yaml.safe_load(y):
            print(pool)



if __name__ == '__main__':
    getAsDictYAML('exampleRetention.yaml')
