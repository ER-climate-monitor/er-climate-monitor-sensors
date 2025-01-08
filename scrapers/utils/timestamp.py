from datetime import datetime, timedelta

class TimestampUtils:
    def __init__(self) -> None:
        self.now = datetime.now()

    def get_compliant_now_timestamp(self):
        return self.get_compliant_timestamp(self.now)

    def get_compliant_timestamp(self, date: datetime)-> int:
        return int((date.replace(minute=0, second=0, microsecond=0).timestamp() / 1000) * 1000000)

    def get_week_timestamps(self):
        now = self.get_compliant_now_timestamp()
        dates = [now]
        base = datetime.fromtimestamp(now / 1000)
        for i in range(6):
            old_date = base - timedelta(days=i+1)
            aligned_date = self.get_compliant_timestamp(old_date)
            dates.append(aligned_date)
        return dates

