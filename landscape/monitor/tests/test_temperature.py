import os
import tempfile

from landscape.monitor.temperature import Temperature
from landscape.lib.tests.test_sysstats import ThermalZoneTest
from landscape.tests.helpers import MonitorHelper
from landscape.tests.mocker import ANY


class TemperatureTestWithSampleData(ThermalZoneTest):
    """Tests for the temperature plugin."""

    helpers = [MonitorHelper]

    def setUp(self):
        """Initialize test helpers and create a sample thermal zone."""
        super(TemperatureTestWithSampleData, self).setUp()
        self.mstore.set_accepted_types(["temperature"])
        self.write_thermal_zone("ZONE1", "50 C")

    def test_wb_disabled_with_no_thermal_zones(self):
        """
        When no thermal zones are available /proc/acpi/thermal_zone
        will be empty.  In this case, the plugin won't register itself
        to respond to client events such as exchange.
        """
        thermal_zone_path = tempfile.mkdtemp()
        os.rmdir(thermal_zone_path)
        plugin = Temperature(thermal_zone_path=thermal_zone_path)
        self.assertEqual(plugin._thermal_zones, [])

    def test_no_messages_without_thermal_zones(self):
        """
        Messages should never be generated by the plugin when no
        thermal zones are available.
        """
        thermal_zone_path = self.makeDir()
        plugin = Temperature(interval=1, thermal_zone_path=thermal_zone_path)
        self.monitor.add(plugin)
        self.reactor.advance(self.monitor.step_size)
        self.assertEqual(len(self.mstore.get_pending_messages()), 0)

    def test_disjointed_thermal_zone_temperature_changes(self):
        """
        Changing data needs to be tracked according to the thermal
        zone the data is for.  This test ensures that the plugin
        creates messages with changes reported correctly.
        """
        self.write_thermal_zone("ZONE2", "50 C")
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        step_size = self.monitor.step_size
        self.monitor.add(plugin)

        self.reactor.advance(step_size)

        self.write_thermal_zone("ZONE2", "56 C")
        self.reactor.advance(step_size)

        messages = list(plugin.create_messages())
        self.assertEqual(len(messages), 2)

        self.assertEqual(messages[0]["thermal-zone"], "ZONE1")
        self.assertEqual(len(messages[0]["temperatures"]), 2)
        self.assertEqual(messages[0]["temperatures"][0],
                         (step_size, 50.0))
        self.assertEqual(messages[0]["temperatures"][1],
                         (step_size * 2, 50.0))

        self.assertEqual(messages[1]["thermal-zone"], "ZONE2")
        self.assertEqual(len(messages[1]["temperatures"]), 2)
        self.assertEqual(messages[1]["temperatures"][0],
                         (step_size, 50.0))
        self.assertEqual(messages[1]["temperatures"][1],
                         (step_size * 2, 56.0))

    def test_messaging_flushes(self):
        """
        Duplicate message should never be created.  If no data is
        available, a message with an empty C{temperatures} list is
        expected.
        """
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        self.monitor.add(plugin)

        self.reactor.advance(self.monitor.step_size)

        messages = plugin.create_messages()
        self.assertEqual(len(messages), 1)

        messages = plugin.create_messages()
        self.assertEqual(len(messages), 0)

    def test_never_exchange_empty_messages(self):
        """
        The plugin will only create messages when data is available.
        If no data is available when an exchange occurs no messages
        should not be queued.
        """
        self.write_thermal_zone("ZONE2", "50 C")
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        self.monitor.add(plugin)
        self.assertEqual(len(self.mstore.get_pending_messages()), 0)

    def test_exchange_messages(self):
        """
        The temperature plugin queues message when an exchange
        happens.  Each message should be aligned to a step boundary;
        messages collected bewteen exchange periods should be
        delivered in a single message.
        """
        self.write_thermal_zone("ZONE2", "50 C")
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        step_size = self.monitor.step_size
        self.monitor.add(plugin)
        self.reactor.advance(step_size)
        self.monitor.exchange()

        self.assertMessages(self.mstore.get_pending_messages(),
                            [{"type": "temperature",
                              "thermal-zone": "ZONE1",
                              "temperatures": [(step_size, 50.0)]},
                             {"type": "temperature",
                              "thermal-zone": "ZONE2",
                              "temperatures": [(step_size, 50.0)]}])

    def test_no_messages_on_bad_values(self):
        """
        If the temperature is in an unknown format, the plugin won't
        break and no messages are sent.
        """
        self.write_thermal_zone("ZONE1", "UNKNOWN C")
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        step_size = self.monitor.step_size
        self.monitor.add(plugin)
        self.reactor.advance(step_size)
        self.monitor.exchange()

        self.assertMessages(self.mstore.get_pending_messages(), [])

    def test_call_on_accepted(self):
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        self.monitor.add(plugin)

        self.reactor.advance(plugin.registry.step_size)

        remote_broker_mock = self.mocker.replace(self.remote)
        remote_broker_mock.send_message(ANY, ANY, urgent=True)
        self.mocker.replay()

        self.reactor.fire(("message-type-acceptance-changed", "temperature"),
                          True)

    def test_no_message_if_not_accepted(self):
        """
        Don't add any messages at all if the broker isn't currently
        accepting their type.
        """
        self.mstore.set_accepted_types([])
        plugin = Temperature(thermal_zone_path=self.thermal_zone_path,
                             create_time=self.reactor.time)
        self.monitor.add(plugin)
        self.reactor.advance(self.monitor.step_size * 2)
        self.monitor.exchange()

        self.mstore.set_accepted_types(["temperature"])
        self.assertMessages(list(self.mstore.get_pending_messages()), [])
