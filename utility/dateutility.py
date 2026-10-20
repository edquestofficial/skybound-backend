from datetime import datetime, timedelta


def ist_now():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)) \
        .strftime("%Y-%m-%d %H:%M:%S")