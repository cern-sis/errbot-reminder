from datetime import date, datetime, time, timedelta

from errbot import BotPlugin, botcmd

# Daily / Retrospective --> If it's an ordinary day or a retrospective, meeting at 9:30
# Sprint Planning --> If it's a Sprint planning, meeting at 15:30
# Sprint review --> If it's a Sprint Review, meeting at 14:45
#  -----------


class Reminder(BotPlugin):
    def get_monday(self):
        today_weekday = date.today().weekday()
        monday = date.today() - timedelta(days=today_weekday)
        monday = datetime.combine(monday, datetime.min.time())
        return monday

    def is_sprint_planning(self):
        first_iteration_startdate = datetime(2022, 2, 28)
        nb_days = first_iteration_startdate - self.get_monday()
        nb_weeks = nb_days / 7
        nb_weeks = int(nb_weeks.total_seconds())

        return nb_weeks % 2 == 0

    EVENTS = {
        "Sprint planning": (datetime(2022, 2, 28, 15, 30), timedelta(weeks=2)),
        "Sprint review": (datetime(2022, 3, 10, 14, 45), timedelta(weeks=2)),
        "Sprint restrospective": (datetime(2022, 3, 11, 9, 30), timedelta(weeks=2)),
        "Daily meeting": (datetime(2022, 3, 1, 9, 30), timedelta(days=1)),
    }

    def next_planning(self):
        today = datetime.now()
        next_planning = self.EVENTS.get("Sprint planning")[0]
        delta_planning = self.EVENTS.get("Sprint planning")[1]

        while next_planning <= today:
            next_planning += delta_planning

        if next_planning > today:
            return next_planning

    def next_review(self):
        today = datetime.now()
        next_review = self.EVENTS.get("Sprint review")[0]
        delta_review = self.EVENTS.get("Sprint review")[1]

        while next_review <= today:
            next_review += delta_review

        if next_review > today:
            return next_review

    def next_retrospective(self):
        today = datetime.now()
        next_retrospective = self.EVENTS.get("Sprint restrospective")[0]
        delta_restrospective = self.EVENTS.get("Sprint restrospective")[1]

        while next_retrospective <= today:
            next_retrospective += delta_restrospective

        if next_retrospective > today:
            return next_retrospective

    def next_daily(self):
        today = datetime.now()
        next_daily = self.EVENTS.get("Daily meeting")[0]
        delta_daily = self.EVENTS.get("Daily meeting")[1]

        while next_daily <= today:
            next_daily += delta_daily

        if self.is_sprint_planning():
            if next_daily.weekday() == 0:
                next_daily += delta_daily

            if next_daily.weekday() >= 5:
                next_daily += timedelta(days=(7 - next_daily.weekday()))

        else:
            if next_daily.weekday() >= 3:
                next_daily += timedelta(days=(7 - next_daily.weekday() + 1))

        return next_daily

    @botcmd
    def reminder_next(self, msg, args):
        return "\n".join(
            f"Next planning : {self.next_planning()}",
            f"Next daily : {self.next_daily()}",
            f"Next review : {self.next_review()}"
            f"Next retrospective : {self.next_retrospective()}",
        )

    @botcmd
    def notify_for_daily_meeting(self, msg, args):
        stream = msg._from._room._id
        topic = msg._from._room._subject

        client = self._bot.client

        day_of_the_week = datetime.now().weekday()
        current_time = datetime.now().replace(second=0, microsecond=0)
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

            meeting_datetime = datetime.combine(datetime.now().date(), meeting_time)

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
