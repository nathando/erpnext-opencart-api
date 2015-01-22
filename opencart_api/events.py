"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: All Events
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import oc_requests, sync_info
from item_qty import update_item_qty
from item_groups import get_child_groups
from datetime import datetime
from frappe.utils import get_files_path, flt, cint
import frappe, json, os, traceback, base64

# ========== Event Handlers for those transactions that affect Item Quantity ==========
# Purchase Receipt Submitted
def oc_pr_submitted(doc, method=None):
    for row in doc.get('purchase_receipt_details'):
        update_item_qty(row.get('item_code'))
# Canceled
def oc_pr_canceled(doc, method=None):
    for row in doc.get('purchase_receipt_details'):
        update_item_qty(row.get('item_code'))


# Delivery Note Submitted
def oc_dn_submitted(doc, method=None):
    for row in doc.get('delivery_note_details'):
        update_item_qty(row.get('item_code'))
# Canceled
def oc_dn_canceled(doc, method=None):
    for row in doc.get('delivery_note_details'):
        update_item_qty(row.get('item_code'))


# Stock Transfer Submitted/Canceled
def oc_se_changed(doc, method=None):
    for row in doc.get('mtn_details'):
        update_item_qty(row.get('item_code'))
