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
OC_PROD_ID = 'oc_product_id'
API_MAP = {
    'products_add': {
        'url': '/api/rest/products/',
        'method': 'POST'
    },
    'products_update': {
        'url': '/api/rest/products/{id}',
        'method': 'PUT'
    }
}

# Construct the URL and get/post/put
def request_oc_url (site_doc, headers, data, url_type, url_params=None):
    # Create new connection
    try:
        conn = httplib.HTTPConnection(site_doc.get('server_base_url'))
        # Add Headers
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"

        # Encode data from a dict
        data = json.dumps(data)

        # Map URL with url params
        url = API_MAP[url_type]['url']
        if url_params is not None:
            url = url.format(**url_params)

        # Request
        conn.request(API_MAP[url_type]['method'], url, data, headers)
        resp = conn.getresponse()

        # Read response
        content = resp.read()
        conn.close()

        return content

    except Exception as e:
        frappe.throw('Error occured: ' + str(e))
        frappe.get_logger().error("Unexpected exception: " +  str(e) + '. Traceback: ' + traceback.format_exc())


# Get quantity if updating, otherwise return 0
def get_quantity(doc, is_updating=False):
    # Updating, return real qty
    if (is_updating):
        return 0
    # Adding, return 0
    else:
        return 0

# Insert Item
@authenticated_opencart
def oc_update_item (doc, site_doc, headers, method=None):
    #
    is_updating = doc.get(OC_PROD_ID) and doc.get(OC_PROD_ID) > 0
    # Get quantity
    qty = get_quantity(doc, is_updating=is_updating)
    data = {
    	"model": doc.get('item_code'),
    	"sku": doc.get('item_code'),
    	"quantity" : qty,
    	"price": doc.get('item_code'),
    	"tax_class_id": "1",
    	"manufacturer_id": "1",
    	"sort_order": "1",
    	"status": doc.get('oc_enable'),
        "product_store": ["0"],
        "product_description": {
    		"1":{
    			"name": doc.get('item_name'),
    			"meta_keyword" : "test product meta_keyword",
                "meta_description" : "test product meta_description",
    			"description" : doc.get('description') or ''
    		}
    	}
    }
    if method != 'on_update':
        frappe.throw('Unknown method %s'%method)

    # Push change to server
    response = request_oc_url(site_doc, headers, data, 'products_add') if not is_updating \
                else request_oc_url(site_doc, headers, data, 'products_update', url_params={'id': doc.get(OC_PROD_ID)})

    # Parse json
    try:
        response_json = json.loads(response)
    except Exception as e:
        frappe.throw('Response has invalid format %s'%response)

    # Check success
    action = 'updated' if is_updating else 'added'
    if (not response_json.get('success')):
        frappe.msgprint('Product not %s. Error: %s' %(action, response_json.get('error')))
    else:
        if (not is_updating):
            doc.update({OC_PROD_ID: response_json.get('product_id')})
            doc.save()
        frappe.msgprint('Product successfully %s'%action)

def oc_delete_item (doc, method=None):
    pass


# OC fields
# product_description (array[ProductDescription], optional),
# model (string): Product model,
# sku (string, optional): Stock Keeping Unit,
# quantity (integer): Quantity,
# price (float): Price,
# tax_class_id (integer): Tax Class Identifier,
# manufacturer_id (integer): Manufacturer ID,
# sort_order (integer): Sort order,
# product_store (array[integer]): List of stores,
# product_category (array[integer], optional): List of categories,
# points (integer, optional): points,
# shipping (integer, optional): shipping,
# stock_status_id (integer, optional): stock_status_id,
# upc (string, optional): upc,
# ean (string, optional): ean,
# jan (string, optional): jan,
# isbn (string, optional): isbn,
# mpn (string, optional): mpn,
# location (string, optional): location,
# date_available (date, optional): date_available,
# weight (float, optional): weight,
# weight_class_id (integer, optional): weight_class_id,
# length (float, optional): length,
# width (float, optional): width,
# height (float, optional): height,
# length_class_id (integer, optional): length_class_id,
# subtract (integer, optional): subtract,
# minimum (integer, optional): minimum,
# status (integer) = ['1-Enabled' or '0-Disabled']: Product status
