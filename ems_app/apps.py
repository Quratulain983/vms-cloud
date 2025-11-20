# import sys
# import threading
# import time
# from datetime import date, timedelta

# from django.apps import AppConfig
# from django.db import connection
# from django.utils import timezone


# class PrintDjangoThread(threading.Thread):
#     def __init__(self, interval=1):  # interval in seconds
#         super().__init__()
#         self.interval = interval
#         self.running = True

#     def run(self):
#         try:
#             # Ensure required tables exist before importing models
#             tables = connection.introspection.table_names()
#             if "ems_app_subscription" not in tables or "ems_app_invoicetable" not in tables:
#                 print("Required tables do not exist. Thread not started.")
#                 return

#             from ems_app.models import (  # Safe to import now
#                 Gateways,
#                 InvoiceTable,
#                 Subscription,
#             )
#         except Exception as e:
#             print(f"Error importing models or checking tables: {e}")
#             return

#         while self.running:
#             try:
#                 print("Checking invoice statuses...")
#                 active_subs = Subscription.objects.filter(status="Active", deactive__isnull=True)
#                 for sub in active_subs:
#                     invoice = InvoiceTable.objects.filter(subscription=sub).order_by('-end_date').first()
#                     if invoice:
#                         if invoice.status == "Paid":
#                             continue
#                         else:
#                             current_date = date.today()
#                             print(invoice.end_date)
#                             print(current_date)
#                             if invoice.end_date >= current_date:
#                                 print(f"Subscription {sub.sub_id}: this id is stop")
#                                 sub.deactive = invoice.end_date
#                                 sub.status = "Deactive"
#                                 sub.save()
#                             else:
#                                 print(f"Subscription {sub.sub_id}: time continue")
#                     else:
#                         print(f"Subscription {sub.sub_id}: No invoice found")
#             except Exception as e:
#                 print(f"Error inside thread loop: {e}")

#             time.sleep(self.interval)

#     def stop(self):
#         self.running = False



# class GatewayStatusThread(threading.Thread):
#     """Thread to auto-set gateway offline if last_seen timeout expires"""
#     def __init__(self, interval=60):  # run every 60 seconds
#         super().__init__()
#         self.interval = interval
#         self.running = True

#     def run(self):
#         try:
#             # Check table exists before import
#             tables = connection.introspection.table_names()
#             if "ems_app_gateways" not in tables:
#                 print("Gateway table missing. Gateway thread not started.")
#                 return

#             from ems_app.models import Gateways

#         except Exception as e:
#             print(f"Error importing gateway model: {e}")
#             return

#         while self.running:
#             try:
#                 print("Running auto-offline gateway check...")
#                 timeout_minutes = 2
#                 cutoff = timezone.now() - timedelta(minutes=timeout_minutes)

#                 Gateways.objects.filter(last_seen__lt=cutoff).update(status=False)

#             except Exception as e:
#                 print(f"Error in gateway status thread: {e}")

#             time.sleep(self.interval)

#     def stop(self):
#         self.running = False


# class EmsAppConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "ems_app"

#     def ready(self):
#         # Only start the thread during 'runserver'
#        # if "runserver" not in sys.argv:
#             return

#         #thread = PrintDjangoThread(interval=1)
#        # thread.daemon = True  # Optional: thread will exit when main program exits
#         #thread.start()



import sys
import threading
import time
from datetime import date, timedelta

from django.apps import AppConfig
from django.db import connection
from django.utils import timezone  # ✅ FIXED — correct timezone


class PrintDjangoThread(threading.Thread):
    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        try:
            tables = connection.introspection.table_names()
            if "ems_app_subscription" not in tables or "ems_app_invoicetable" not in tables:
                print("Required tables do not exist. Thread not started.")
                return

            from ems_app.models import InvoiceTable, Subscription
        except Exception as e:
            print(f"Error importing models: {e}")
            return

        while self.running:
            try:
                active_subs = Subscription.objects.filter(status="Active", deactive__isnull=True)
                for sub in active_subs:
                    invoice = InvoiceTable.objects.filter(subscription=sub).order_by('-end_date').first()
                    if invoice:
                        if invoice.status != "Paid":
                            current_date = date.today()
                            if invoice.end_date >= current_date:
                                sub.deactive = invoice.end_date
                                sub.status = "Deactive"
                                sub.save()
            except Exception as e:
                print(f"Invoice thread error: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.running = False


class GatewayStatusThread(threading.Thread):
    def __init__(self, interval=60):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        try:
            tables = connection.introspection.table_names()
            if "ems_app_gateways" not in tables:
                print("Gateway table missing. Thread not started.")
                return

            from ems_app.models import Gateways
        except Exception as e:
            print(f"Error importing Gateway model: {e}")
            return

        while self.running:
            try:
                print("Running auto-offline gateway check...")
                timeout_minutes = 2
                cutoff = timezone.now() - timedelta(minutes=timeout_minutes)

                Gateways.objects.filter(last_seen__lt=cutoff).update(status=False)

            except Exception as e:
                print(f"Gateway thread error: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.running = False


class EmsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ems_app"

    def ready(self):
        # Start threads ONLY when running "runserver"
        if "runserver" not in sys.argv:
            return

        print("Starting background threads...")

        invoice_thread = PrintDjangoThread(interval=1)
        invoice_thread.daemon = True
        invoice_thread.start()

        gateway_thread = GatewayStatusThread(interval=60)
        gateway_thread.daemon = True
        gateway_thread.start()
