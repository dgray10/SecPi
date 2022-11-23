import json
import logging
import subprocess
import time

from testing.util.events import OLD_ALARM_EVENT
from testing.util.service import ManagerServiceWrapper
from testing.util.service import WebinterfaceServiceWrapper

import testing.test_webinterface
# from test_webinterface import test_webinterface_create_worker
# from test_webinterface import test_webinterface_create_zone
# from test_webinterface import test_webinterface_create_sensor



logger = logging.getLogger(__name__)


def test_manager_start_stop():
    """
    Start Manager and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start service in separate process.
    service = ManagerServiceWrapper()
    service.run()

    # Before shutting down, wait a bit so that we can receive the whole log.
    time.sleep(0.25)

    # Send service a shutdown signal.
    service.shutdown(identifier="m")

    # Read application log.
    app_log = service.read_log()

    # Verify everything is in place.
    assert "Loading configuration from etc/testing/config-manager.toml" in app_log
    # assert "Storing alarms to" in app_log
    # assert "Connecting to database sqlite:///secpi-database-testing.sqlite" in app_log
    # assert "Connecting to database mysql+pymysql://secpi:secret@localhost/secpi-testdrive" in app_log
    assert "Connecting to database postgresql://secpi:secret@localhost/secpi-testdrive" in app_log
    assert "Connecting to AMQP broker <URLParameters host=localhost port=5672 virtual_host=/ ssl=False>" in app_log
    assert "Connecting to AMQP broker successful" in app_log
    assert "Manager is ready" in app_log
    assert "Start consuming AMQP queue" in app_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in app_log
    assert "Stop consuming AMQP queue" in app_log


def test_manager_receive_alarm(manager_service):
    """
    Start Manager and submit an alarm event using AMQP. Verify that the log output matches the expectations.
    """
    service = WebinterfaceServiceWrapper()
    service.run()

    testing.test_webinterface.test_webinterface_create_worker(service)
    testing.test_webinterface.test_webinterface_create_zone(service)
    testing.test_webinterface.test_webinterface_create_sensor(service)

    # Submit an alarm signal.
    command = f"""echo '{json.dumps(OLD_ALARM_EVENT)}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.55)

    # Read application log.
    app_log = manager_service.read_log()

    # Send service a shutdown signal.
    service.shutdown()

    # Verify everything is in place.
    assert (
        "Received late alarm:" in app_log
        and '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    )
    # assert "Created directory for alarm:" in app_log
    # assert "[LATE] Alarm from sensor id=1, worker id=1: Got TCP connection, raising alarm" in app_log
    assert "[LATE] Alarm from sensor testdrive-sensor, worker testdrive-worker: Got TCP connection, raising alarm"\
           in app_log
    assert "Executing actions" in app_log
    assert "Starting to wait for action response from workers" in app_log
    assert "Waiting for action response from workers" in app_log
