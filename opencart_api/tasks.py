# Copyright (c) 2015, Nathan @ Hoovix Pte. Ltd.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe.utils import nowdate, add_days
from utils import sync_info, sync_log_create
from items import sync_all_items
from item_groups import sync_child_groups

EMAIL_SENDER = "scheduler@abc.com"
EMAIL_SUBJECT = "[%s] Opencart syncing %s "

@frappe.whitelist()
def daily():
    # Get all oc sites
    site_names = frappe.db.sql("""select name from `tabOpencart Site`""")
    logs=["<b>Sync Log on date: %s</b>"% datetime.now().strftime("%d-%b-%y")]
    success=True
    # Sync
    for name in site_names:
        name = name[0]
        logs.append("Opencart Site: %s"%name)
        site_doc = frappe.get_doc("Opencart Site", name)

        # Sync groups and record log
        logs.append("Sync Item Groups")
        results = sync_child_groups(site_doc.get('root_item_group'), name, site_doc.get('server_base_url'), \
            site_doc.get('api_map'), site_doc.get('opencart_header_key'), site_doc.get('opencart_header_value'), silent=True)
        logs += results.get('logs')
        success = success and results.get('success')

        # Sync items and record log
        logs.append("Sync Items")
        results_item = sync_all_items(site_doc.get('server_base_url'), site_doc.get('api_map'), \
            site_doc.get('opencart_header_key'), site_doc.get('opencart_header_value'), silent=True)
        logs += results_item.get('logs')
        success = success and results.get('success')

        # Send mail if unsuccessful
        logs = ['<p>%s</p>'%x for x in logs]
        frappe.sendmail(recipients=[str(site_doc.get('user'))],
            sender=EMAIL_SENDER,
            subject=EMAIL_SUBJECT%(datetime.now().strftime("%d-%b-%y"), "succeeded" if success else "failed"), message='</br>'.join(logs))

    return {'success': success}
