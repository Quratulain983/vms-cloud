from django.apps import AppConfig
import threading
import time
from datetime import date
import sys
from django.db import connection


class PrintDjangoThread(threading.Thread):
    def __init__(self, interval=1):  # interval in seconds
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        try:
            # Ensure required tables exist before importing models
            tables = connection.introspection.table_names()
            if "ems_app_subscription" not in tables or "ems_app_invoicetable" not in tables:
                print("Required tables do not exist. Thread not started.")
                return

            from ems_app.models import Subscription, InvoiceTable  # Safe to import now
        except Exception as e:
            print(f"Error importing models or checking tables: {e}")
            return

        while self.running:
            try:
                print("Checking invoice statuses...")
                active_subs = Subscription.objects.filter(status="Active", deactive__isnull=True)
                for sub in active_subs:
                    invoice = InvoiceTable.objects.filter(subscription=sub).order_by('-end_date').first()
                    if invoice:
                        if invoice.status == "Paid":
                            continue
                        else:
                            current_date = date.today()
                            print(invoice.end_date)
                            print(current_date)
                            if invoice.end_date >= current_date:
                                print(f"Subscription {sub.sub_id}: this id is stop")
                                sub.deactive = invoice.end_date
                                sub.status = "Deactive"
                                sub.save()
                            else:
                                print(f"Subscription {sub.sub_id}: time continue")
                    else:
                        print(f"Subscription {sub.sub_id}: No invoice found")
            except Exception as e:
                print(f"Error inside thread loop: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.running = False


class EmsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ems_app"

    def ready(self):
        # Only start the thread during 'runserver'
       # if "runserver" not in sys.argv:
            return

        #thread = PrintDjangoThread(interval=1)
       # thread.daemon = True  # Optional: thread will exit when main program exits
        #thread.start()
