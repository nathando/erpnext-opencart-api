"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
import frappe, json, os, traceback
import httplib, urllib

# Temp Map of APIs (Store it some where ?)
API_MAP = {
    'products_add': {
        'url': '/api/rest/products/',
        'method': 'GET'
    }
}

# Construct the URL and get/post/put
def request_oc_url (site_doc, headers, data, url_type):
    # Create new connection
    try:
        conn = httplib.HTTPConnection(site_doc.get('server_base_url'))
        # Add Headers
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"

        # Encode data from a dict
        data = urllib.urlencode(data)

        # Request
        conn.request(API_MAP[url_type]['method'], API_MAP[url_type]['url'], data, headers)
        resp = conn.getresponse()

        # Read response
        content = resp.read()
        conn.close()

    except Exception as e:
        frappe.throw('Error occured: ' + str(e))
        frappe.get_logger().error("Unexpected exception: " +  str(e) + '. Traceback: ' + traceback.format_exc())

# Insert Item
@authenticated_opencart
def oc_update_item (doc, site_doc, headers, method=None):

    data = {
    	"model": doc.get('item_code'),
    	"sku": doc.get('item_code'),
    	"quantity" : doc.get('qty'),
    	"price": doc.get('item_code'),
    	"tax_class_id": "1",
    	"manufacturer_id": "1",
    	"sort_order": "1",
    	"status": "1",
        "product_store": "0",
        "product_description": {
    		"1":{
    			"name": doc.get('item_name'),
    			"meta_description" : "test product meta_description",
    			"meta_keyword" : "test product meta_keyword",
    			"description" : "test product description"
    		}

    	}
    }
    # if method in ['on_update', 'on_submit']:
    request_oc_url(site_doc, headers, data, 'products_add')


def oc_disable_item (doc, method=None):
    pass

def oc_delete_item (doc, method=None):
    pass
