from datetime import date, datetime, time, timedelta

from errbot import BotPlugin, botcmd

# Daily / Retrospective --> If it's an ordinary day or a retrospective, meeting at 9:30
# Sprint Planning --> If it's a Sprint planning, meeting at 15:30
# Sprint review --> If it's a Sprint Review, meeting at 14:45
#  -----------------


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

        if nb_weeks % 2 == 0:
            return True

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
