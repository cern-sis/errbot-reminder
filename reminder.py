from datetime import date, datetime, timedelta

import pytz
from errbot import BotPlugin, botcmd
import re

# Daily / Retrospective --> If it's an ordinary day or a retrospective, meeting at 9:30
# Sprint Planning --> If it's a Sprint planning, meeting at 15:30
# Sprint review --> If it's a Sprint Review, meeting at 14:45

#  -----------------

utc = pytz.timezone("UTC")
now = utc.localize(datetime.utcnow())
tz_cern = pytz.timezone("Europe/Zurich")
now.astimezone(tz_cern)


EVENTS = {
    "sprint planning": (
        tz_cern.localize(datetime(2022, 2, 28, 15, 00)),
        timedelta(weeks=2),
    ),
    "review": (
        tz_cern.localize(datetime(2022, 3, 10, 14, 45)),
        timedelta(weeks=2),
    ),
    "Retrospective": (
        tz_cern.localize(datetime(2022, 3, 11, 9, 30)),
        timedelta(weeks=2),
    ),
    "daily": (
        tz_cern.localize(datetime(2022, 3, 1, 9, 30)),
        timedelta(days=1),
    ),
}

CONFIG = {
    "ts_stream_id":  311658,
    "zoom_url_regex":  re.compile('https://cern.zoom.us/j/\d+\?pwd=\w+'),
}


class Reminder(BotPlugin):
    @staticmethod
    def get_monday(today):
        today_weekday = today.weekday()
        monday = today.date() - timedelta(days=today_weekday)
        monday = datetime.combine(monday, datetime.min.time())
        return monday.date()

    @staticmethod
    def is_sprint_planning(today):
        first_iteration_startdate = date(2022, 2, 28)
        nb_days = (first_iteration_startdate - Reminder.get_monday(today)).days
        nb_weeks = nb_days // 7

        return nb_weeks % 2 == 0

    @staticmethod
    def next_occurance(meeting, today):
        today = tz_cern.localize(today)
        next_occurance = EVENTS.get(meeting)[0].astimezone(tz_cern)
        delta_occurance = EVENTS.get(meeting)[1]

        while next_occurance <= today:
            next_occurance += delta_occurance

        if next_occurance > today:
            return next_occurance.strftime("**%Y-%m-%d** at **%H:%M**")

    @staticmethod
    def next_daily(today):
        today = tz_cern.localize(today)
        next_daily = EVENTS.get("daily")[0].astimezone(tz_cern)
        delta_daily = EVENTS.get("daily")[1]

        while next_daily <= today:
            next_daily += delta_daily

            if Reminder.is_sprint_planning(today):
                if next_daily.weekday() == 0:
                    next_daily += delta_daily

                if next_daily.weekday() >= 5:
                    next_daily += timedelta(days=(7 - next_daily.weekday()))

            else:
                if next_daily.weekday() >= 3:
                    next_daily += timedelta(days=(7 - next_daily.weekday() + 1))

        return next_daily.strftime("**%Y-%m-%d** at **%H:%M**")

    def zoom_meeting_url(self):
        client = self._bot.client
        # Get stream by id is currently not available on the python client.
        response = client.get_streams(
            include_public = False,
        )

        stream = next(filter(
            lambda s: s["stream_id"] == CONFIG["ts_stream_id"],
            response["streams"],
        ))
        match = CONFIG["zoom_url_regex"].search(stream["description"])

        return match.group()

    @botcmd
    def reminder_link(self, msg, args):
        return f"[Link]({self.zoom_meeting_url()}) to our Zoom meeting"

    @botcmd
    def reminder_next(self, msg, args):
        today = datetime.now()
        next_planning = Reminder.next_occurance("sprint planning", today)
        next_daily = Reminder.next_daily(today)
        next_review = Reminder.next_occurance("review", today)
        next_retrospective = Reminder.next_occurance("Retrospective", today)
        return "\n".join(
            [
                f"Next planning: {next_planning}",
                f"Next daily: {next_daily}",
                f"Next review: {next_review}",
                f"Next retrospective: {next_retrospective}",
            ]
        )

    def send_notification(self, meeting, today):
        client = self._bot.client
        next_occurance = EVENTS.get(meeting)[0]
        delta_occurance = EVENTS.get(meeting)[1]

        while next_occurance <= today:
            next_occurance += delta_occurance

        if next_occurance > today:
            if next_occurance.date() == today.date():
                now_minus_15 = (next_occurance - timedelta(minutes=15)).time()
                now_minus_5 = (next_occurance - timedelta(minutes=5)).time()

                zoom_link = self.zoom_meeting_url()

                if now_minus_15 == today.time():
                    client.send_message(
                        {
                            "type": "stream",
                            "to": "tools & services",
                            "topic": meeting,
                            "content": f"@**all** [meeting]({zoom_link}) in 15 minutes.",
                        }
                    )

                if now_minus_5 == today.time():
                    client.send_message(
                        {
                            "type": "stream",
                            "to": "tools & services",
                            "topic": meeting,
                            "content": f"@**all** [meeting]({zoom_link}) in 5 minutes.",
                        }
                    )

    def notify_for_meetings(self):
        today = (datetime.now().astimezone(tz_cern)).replace(second=0, microsecond=0)
        weekday = today.weekday()

        if weekday < 5:
            if weekday == 0 and self.is_sprint_planning(today):
                self.send_notification("sprint planning", today)

            elif weekday == 4 and not self.is_sprint_planning(today):
                self.send_notification("Retrospective", today)

            elif weekday == 3 and not self.is_sprint_planning(today):
                self.send_notification("daily", today)
                self.send_notification("review", today)

            else:
                self.send_notification("daily", today)

    def activate(self):
        super().activate()
        self.start_poller(60, self.notify_for_meetings)
