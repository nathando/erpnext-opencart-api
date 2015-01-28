"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product quantity functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart, get_only
from utils import oc_requests, sync_info
from datetime import datetime
from frappe.utils import get_files_path, flt, cint
import frappe, json, os, traceback, base64
OC_PROD_ID = 'oc_product_id'
OC_CAT_ID = 'opencart_category_id'

# Update item quantity
@authenticated_opencart
def update_item_qty_handler(doc, site_doc, api_map, headers, silent=False):
    logs = []
    success = False
    qty = get_item_qty(doc)

    # Cannot find product id -> cannot sync
    if (not doc.get(OC_PROD_ID)):
        sync_info(logs, 'Product ID for Opencart is missing', stop=True, silent=silent, error=True)

    data = [{
        "product_id": doc.get(OC_PROD_ID),
        "quantity": str(cint(qty))
    }]

    # Push qty to opencart
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, 'Product Quantity', stop=False, data=data)
    if res:
        # Not successful
        if (not res.get('success')):
            sync_info(logs, 'Quantity for product %s not updated on Opencart. Error: %s' %(doc.get('name'), res.get('error')), stop=False, silent=silent, error=True)
        else:
            success = True
            sync_info(logs, 'Quantity for product %s successfully updated on Opencart'%doc.get('name'), stop=False, silent=silent)
    return {
        'success': success,
        'logs': logs
    }

@frappe.whitelist()
def update_item_qty(doc_name, silent=False):
    item = frappe.get_doc("Item", doc_name)
    return update_item_qty_handler(item, silent=silent)

# Return the current qty of item based on item code (or Item Doc Name)
@frappe.whitelist()
def get_item_qty_by_name(doc_name):
    item = frappe.get_doc("Item", doc_name)
    return get_item_qty(item)

# TODO: Write test to make sure this function is correct. Note: current query all transaction.
# This can create overhead time.
def get_item_qty(item):
    # Query stock ledger to get qty
    item_ledgers = frappe.db.sql("""select item_code, warehouse, posting_date, actual_qty, valuation_rate, \
        stock_uom, company, voucher_type, qty_after_transaction, stock_value_difference \
        from `tabStock Ledger Entry` \
        where docstatus < 2 and item_code = '%s' order by posting_date, posting_time, name""" \
        %item.get('item_code'), as_dict=1)

    # Calculate the qty based purely on stock transaction record
    bal_qty = 0
    for d in item_ledgers:
        if d.voucher_type == "Stock Reconciliation":
            qty_diff = flt(d.qty_after_transaction) - bal_qty
        else:
            qty_diff = flt(d.actual_qty)
        bal_qty += qty_diff

    # Adjust this by Sales Order that've been confirmed but not completely delivered
    sales_order_items = frappe.db.sql("""select * from `tabSales Order Item` where item_code = '%s' \
        and parent in (select name from `tabSales Order` \
        where docstatus < 2 and \
        (per_delivered is NULL or per_delivered != 100))"""%item.get('item_code'), as_dict=1)
    for so_item in sales_order_items:
        bal_qty -= flt(so_item.get('qty'))
        dn_items = frappe.get_list("Delivery Note Item", {'docstatus': 1, 'prevdoc_detail_docname': so_item.get('name')}, ['name', 'qty'])
        if (len(dn_items)>0):
            for dn_item in dn_items:
                 bal_qty += flt(dn_item.get('qty'))
    return len(sales_order_items) if bal_qty!=0 else "0"
