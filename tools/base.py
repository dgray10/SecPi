import json
import logging

logger = logging.getLogger(__name__)


class Service:

    def stop(self):
        self.do_shutdown = True
        self.bus.shutdown()

    def __del__(self):
        try:
            self.stop()

        # If there is no connection object closing won't work.
        except AttributeError:
            logger.info("No connection cleanup possible")

    def got_operational(self, ch, method, properties, body):
        """
        AMQP: Receive and process operational messages.

        Currently, this implements the handler for the shutdown signal, which is mostly
        needed in testing scenarios.

        Usage::

            echo '{"action": "shutdown"}' | amqp-publish --url="amqp://guest:guest@localhost:5672" --routing-key=secpi-op-1
        """
        logger.info(f"Got message on operational channel: {body}")
        try:
            message = json.loads(body)
            action = message.get("action")

            # Invoke shutdown.
            if action == "shutdown":
                self.stop()
        except:
            logger.exception("Processing operational message failed")