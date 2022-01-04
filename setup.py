#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Setup for rqt_rosbag_control """
import os
from setuptools import setup

package_name = 'rqt_rosbag_control'
setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name), ['plugin.xml']),
        ('share/' + package_name + '/resource',
         ['resource/RosbagControl.ui', 'resource/pause.png', 'resource/play.png', 'resource/step_once.png']),
        ('lib/' + package_name, ['scripts/rqt_rosbag_control'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Francisco Miguel Moreno',
    maintainer_email='franmore@ing.uc3m.es',
    description='The rqt_rosbag_control package',
    license='MIT',
    scripts=['scripts/rqt_rosbag_control'],
)
