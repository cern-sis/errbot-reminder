from datetime import date, datetime, timedelta  # , timezone, time

import pytz
from errbot import BotPlugin, botcmd

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
        tz_cern.localize(datetime(2022, 2, 28, 15, 30)),
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
        tz_cern.localize(datetime(2022, 3, 1, 15, 30)),
        timedelta(days=1),
    ),
}


class Reminder(BotPlugin):
    @staticmethod
    def get_monday(today):
        today_weekday = today.weekday()
        monday = date.today() - timedelta(days=today_weekday)
        monday = datetime.combine(monday, datetime.min.time())
        return monday.date()

    @staticmethod
    def is_sprint_planning():
        first_iteration_startdate = date(2022, 2, 28)
        nb_days = (first_iteration_startdate - Reminder.get_monday(date.today())).days
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

            if Reminder.is_sprint_planning():
                if next_daily.weekday() == 0:
                    next_daily += delta_daily

                if next_daily.weekday() >= 5:
                    next_daily += timedelta(days=(7 - next_daily.weekday()))

            else:
                if next_daily.weekday() >= 3:
                    next_daily += timedelta(days=(7 - next_daily.weekday() + 1))

        return next_daily.strftime("**%Y-%m-%d** at **%H:%M**")

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

    def test_cmd(self):
        client = self._bot.client

        today = tz_cern.localize(datetime.now())
        weekday = today.weekday()

        stream = "test"
        topic = "daily"

        if weekday < 5:
            for meet in EVENTS:
                next_occurance = EVENTS.get(meet)[0]
                delta_occurance = EVENTS.get(meet)[1]

                while next_occurance <= today:
                    next_occurance += delta_occurance

                next_occurance = next_occurance.astimezone(tz_cern)

                if next_occurance > today:
                    if next_occurance.date() == today.date():
                        client.send_message(
                            {
                                "type": "stream",
                                "to": stream,
                                "topic": topic,
                                "content": "**Meeting in 15 minutes**",
                            }
                        )
                        client.send_message(
                            {
                                "type": "stream",
                                "to": stream,
                                "topic": topic,
                                "content": f"{today} XX {next_occurance}",
                            }
                        )

    def activate(self):
        super().activate()
        self.start_poller(3, self.test_cmd, times=1)
