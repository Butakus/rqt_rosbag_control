#!/usr/bin/env python
"""
RQT Plugin to control rosbag playback
"""

import os
import time
import threading

from python_qt_binding import loadUi  # pylint: disable=import-error
from python_qt_binding.QtGui import QPixmap, QIcon  # pylint: disable=no-name-in-module, import-error
from python_qt_binding.QtWidgets import QWidget  # pylint: disable=no-name-in-module, import-error
from qt_gui.plugin import Plugin  # pylint: disable=import-error

import rclpy
from ament_index_python.packages import get_package_share_directory
from rosgraph_msgs.msg import Clock
from rosbag2_interfaces.srv import IsPaused, PlayNext, Pause, TogglePaused


class RosbagControlPlugin(Plugin):

    """
    RQT Plugin to control rosbag playback
    """

    def __init__(self, context):
        """
        Constructor
        """
        super(RosbagControlPlugin, self).__init__(context)
        self.setObjectName('Rosbag Control')

        # Set UI
        self._widget = QWidget()

        package_share_dir = get_package_share_directory('rqt_rosbag_control')
        ui_file = os.path.join(package_share_dir, 'resource', 'RosbagControl.ui')

        loadUi(ui_file, self._widget)
        self._widget.setObjectName('RosbagControl')
        if context.serial_number() > 1:
            self._widget.setWindowTitle(
                self._widget.windowTitle() + (' (%d)' % context.serial_number()))

        self.pause_icon = QIcon(
            QPixmap(os.path.join(
                package_share_dir, 'resource', 'pause.png')))
        self.play_icon = QIcon(
            QPixmap(os.path.join(
                package_share_dir, 'resource', 'play.png')))
        self._widget.pushButtonStepOnce.setIcon(
            QIcon(QPixmap(os.path.join(
                package_share_dir, 'resource', 'step_once.png'))))
        self._widget.pushButtonPause.setIcon(self.pause_icon)

        # self._widget.pushButtonPlayPause.setDisabled(True)
        # self._widget.pushButtonStepOnce.setDisabled(True)
        self._widget.pushButtonPlayPause.setIcon(self.play_icon)
        self._widget.pushButtonPlayPause.clicked.connect(self.toggle_play_pause)
        self._widget.pushButtonStepOnce.clicked.connect(self.step_once)
        self._widget.pushButtonPause.clicked.connect(self.pause)

        context.add_widget(self._widget)

        # Set ROS services and clock subscriber
        self._node = rclpy.create_node('rqt_rosbag_control_node')

        self._is_paused_client = self._node.create_client(IsPaused, '/rosbag2_player/is_paused')
        self._pause_client = self._node.create_client(Pause, '/rosbag2_player/pause')
        self._play_next_client = self._node.create_client(PlayNext, '/rosbag2_player/play_next')
        self._toggle_paused_client = self._node.create_client(TogglePaused, '/rosbag2_player/toggle_paused')

        self.clock_subscriber = self._node.create_subscription(Clock, "/clock", self.clock_sub, 10)

        self._running = True

        self._spin_thread = threading.Thread(target=self.spin)
        self._spin_thread.start()
        self._update_paused_thread = threading.Thread(target=self.update_paused)
        self._update_paused_thread.start()

    def toggle_play_pause(self):
        """ Toggle play/pause """
        print("Play/Pause")
        if not self._toggle_paused_client.wait_for_service(timeout_sec=5.0):
            print("WARNING: toggle_paused service not available. Is rosbag player running?")
            return

        req = TogglePaused.Request()
        future = self._toggle_paused_client.call_async(req)

    def step_once(self):
        """ Execute one step """
        print("Play next")
        if not self._play_next_client.wait_for_service(timeout_sec=5.0):
            print("WARNING: play_next service not available. Is rosbag player running?")
            return

        req = PlayNext.Request()
        future = self._play_next_client.call_async(req)

    def pause(self):
        """ Pause bagfile """
        print("Pause")
        if not self._pause_client.wait_for_service(timeout_sec=5.0):
            print("WARNING: pause service not available. Is rosbag player running?")
            return

        req = Pause.Request()
        future = self._pause_client.call_async(req)


    def clock_sub(self, clock_msg):
        """ /clock subscriber """
        clock_str = '{s}.{n}'.format(s=clock_msg.clock.sec, n=clock_msg.clock.nanosec)
        self._widget.labelTimeData.setText(clock_str)

    def set_paused_callback(self, future):
        print("set_paused_callback")
        result = future.result()
        print(F"result: {result}")
        self._widget.labelPausedData.setText(str(result.paused))
        # If not paused, disable play next button (can only be done while playback is paused)
        self._widget.pushButtonStepOnce.setDisabled(not result.paused)

    def update_paused(self):
        while rclpy.ok() and self._running:
            if not self._is_paused_client.wait_for_service(timeout_sec=5.0):
                print("WARNING: is_paused service not available. Is rosbag player running?")
                return

            req = IsPaused.Request()
            result = self._is_paused_client.call(req)

            self._widget.labelPausedData.setText(str(result.paused))
            # If not paused, disable play next button (can only be done while playback is paused)
            self._widget.pushButtonStepOnce.setDisabled(not result.paused)
            # Update play/Pause icon
            if result.paused:
                self._widget.pushButtonPlayPause.setIcon(self.play_icon)
            else:
                self._widget.pushButtonPlayPause.setIcon(self.pause_icon)

            time.sleep(0.05)

    def spin(self):
        """ 
        Spin the node and update the state of
        the playback (paused/unpaused) via service call
        """
        while rclpy.ok() and self._running:
            rclpy.spin_once(self._node, timeout_sec=1.0)
            time.sleep(0.01)

    def shutdown_plugin(self):
        """ shutdown plugin """
        self._running = False
        self._spin_thread.join()
        self._update_paused_thread.join()
        self._node.destroy_node()
