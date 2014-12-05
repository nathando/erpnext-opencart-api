"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
import frappe, json, os, traceback
import httplib

# Temp Map of APIs (Store it some where ?)
API_MAP = {
    'products_add': {
        'url': '/products/',
        'method': 'POST'
    }
}

# Construct the URL and get/post/put
def request_oc_url (site_doc, headers, data, url_type):
    # Create new connection
    conn = httplib.HTTPConnection(site_doc.get('server_base_url'))

    # Add Headers
    headers["Content-type"] = "application/x-www-form-urlencoded"
    headers["Accept"] = "text/plain"
    frappe.throw(headers)

    # Encode data from a dict
    data = urllib.urlencode(data)

    # Request
    conn.request(API_MAP[url_type]['method'], API_MAP[url_type]['url'], data, header)
    resp = conn.getresponse()

    # Validate response
    frappe.thow(resp)

    # Read response
    content = resp.read()

    conn.close()


# Insert Item
@authenticated_opencart
def oc_update_item (doc, site_doc, headers, method=None):
    data = {
        'sku': doc.get('item_code'),
        'name': doc.get('item_name')
    }
    # if method in ['on_update', 'on_submit']:
    request_oc_url(site_doc, headers, data, 'products_add')


def oc_disable_item (doc, method=None):
    pass

def oc_delete_item (doc, method=None):
    pass
