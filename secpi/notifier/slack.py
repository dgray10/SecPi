import logging

from slacker import Slacker

from secpi.model.message import NotificationMessage
from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class SlackNotifier(Notifier):
    def __init__(self, identifier, params):
        super(SlackNotifier, self).__init__(identifier, params)
        if "bot_token" not in params or "channel" not in params:
            self.corrupted = True
            logger.error("Slack: Token or channel name missing")
            return

    def notify(self, info: NotificationMessage):
        if not self.corrupted:
            try:
                logger.debug("Sending Slack notification")

                # Render the notification message.
                info_str = info.render_message()

                channel_name = self.params["channel"]
                slack = Slacker(self.params["bot_token"])

                # groups are private chats
                channels = slack.groups.list(1)  # 1 --> exclude archived
                channel = [c for c in channels.body["groups"] if c["name"] == channel_name]

                if len(channel) > 0:
                    # we got a channel
                    channel_id = channel[0]["id"]
                    logger.debug("Got existing channel")
                else:
                    # if not exists, create it
                    logger.debug("No channel found, creating one")
                    new_channel_req = slack.groups.create(channel_name)

                    channel_id = new_channel_req.body["group"]["id"]

                if channel_id is not None:
                    logger.debug("Found channel: %s" % channel_id)
                    slack.chat.post_message(channel_name, info_str)

                else:
                    logger.error("No channel found")
            except KeyError as ke:
                logger.error("Error in Slack Notifier: %s" % ke)

        else:
            logger.error("Slack Notifier corrupted. No token or channel name given as parameter.")

    def cleanup(self):
        logger.debug("Slack Notifier: No cleanup necessary at the moment.")
