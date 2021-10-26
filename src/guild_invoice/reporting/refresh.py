import datetime
import time

from django.db import transaction, connection


from .models import RefreshLog

@transaction.atomic
def refresh_reports():
    start_time = time.monotonic()
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY reports_usersignup")
    end_time = time.monotonic()
    RefreshLog.objects.create(duration=datetime.timedelta(seconds=end_time - start_time))
