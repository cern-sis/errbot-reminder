from datetime import date, datetime, time, timedelta, timezone

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

    EVENTS = {
        "Sprint planning": (
            tz_cern.localize(datetime(2022, 2, 28, 15, 30)),
            timedelta(weeks=2),
        ),
        "Sprint review": (
            tz_cern.localize(datetime(2022, 3, 10, 14, 45)),
            timedelta(weeks=2),
        ),
        "Sprint retrospective": (
            tz_cern.localize(datetime(2022, 3, 11, 9, 30)),
            timedelta(weeks=2),
        ),
        "Daily meeting": (
            tz_cern.localize(datetime(2022, 3, 1, 9, 30)),
            timedelta(days=1),
        ),
    }

    @staticmethod
    def next_occurance(meeting, today):
        today = tz_cern.localize(today)
        next_occurance = Reminder.EVENTS.get(meeting)[0].astimezone(tz_cern)
        delta_occurance = Reminder.EVENTS.get(meeting)[1]

        while next_occurance <= today:
            next_occurance += delta_occurance

        if next_occurance > today:
            return next_occurance.strftime("**%Y-%m-%d** at **%H:%M**")

    @staticmethod
    def next_daily(today):
        today = tz_cern.localize(today)
        next_daily = Reminder.EVENTS.get("Daily meeting")[0].astimezone(tz_cern)
        delta_daily = Reminder.EVENTS.get("Daily meeting")[1]

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
        next_planning = Reminder.next_occurance("Sprint planning", today)
        next_daily = Reminder.next_daily(today)
        next_review = Reminder.next_occurance("Sprint review", today)
        next_retrospective = Reminder.next_occurance("Sprint retrospective", today)
        return "\n".join(
            [
                f"Next planning: {next_planning}",
                f"Next daily: {next_daily}",
                f"Next review: {next_review}",
                f"Next retrospective: {next_retrospective}",
            ]
        )

    @botcmd
    def notify_for_daily_meeting(self, msg, args):
        stream = msg._from._room._id

        client = self._bot.client

        day_of_the_week = datetime.now(timezone).weekday()
        current_time = datetime.now(timezone).replace(second=0, microsecond=0)
        stream = "tools & services"

        if day_of_the_week != 5 and day_of_the_week != 6:
            if date.today().weekday() == 0 and self.is_sprint_planning():
                meeting_time = time(15, 30)
                topic = "sprint planning"

            elif date.today().weekday() == 3 and not self.is_sprint_planning():
                meeting_time = time(14, 45)
                topic = "sprint review"

            elif date.today().weekday == 4 and not self.is_sprint_planning():
                meeting_time = time(9, 30)
                topic = "retrospective"

            else:
                meeting_time = time(9, 30)
                topic = "daily"

            meeting_datetime = datetime.combine(
                datetime.now(timezone).date(), meeting_time
            )

            if (
                current_time.hour == meeting_datetime.hour
                and current_time.minute == meeting_datetime.minute - 15
            ):
                client.send_message(
                    {
                        "type": "stream",
                        "to": stream,
                        "topic": topic,
                        "content": "Meeting in 15 minutes",
                    }
                )

            if (
                current_time.hour == meeting_datetime.hour
                and current_time.minute == meeting_datetime.minute - 5
            ):
                client.send_message(
                    {
                        "type": "stream",
                        "to": stream,
                        "topic": topic,
                        "content": "Meeting in 5 minutes",
                    }
                )

    def activate(self):
        super().activate()
        self.start_poller(60, self.notify_for_daily_meeting(None, None, None))
