"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import request_oc_url
from item_groups import get_child_groups
from datetime import datetime
import frappe, json, os, traceback

OC_PROD_ID = 'oc_product_id'

# Get quantity if updating, otherwise return 0
def get_quantity(doc, is_updating=False):
    # Updating, return real qty
    if (is_updating):
        return 0
    # Adding, return 0
    else:
        return 0

# Insert/Update Item
@authenticated_opencart
def oc_update_item (doc, site_doc, api_map, headers, method=None):
    # Check method
    if method != 'on_update':
        frappe.throw('Unknown method %s'%method)
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
    # Get API obj
    api_obj = api_map.get('Product Add')
    api_params = None
    if is_updating:
        api_obj = api_map.get('Product Edit')
        api_params = {'id': doc.get(OC_PROD_ID)}
    if (api_obj is None):
        frappe.throw('Missing API URL for adding/updating product')

    # Push change to server
    response = request_oc_url(site_doc.get('server_base_url'), headers, data, api_obj, url_params = api_params)

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

@authenticated_opencart
def oc_delete_item (doc, site_doc, api_map, headers, method=None):
    # Check method
    if method != 'on_trash':
        frappe.throw('Unknown method %s'%method)
    # Push delete on oc server
    api_obj = api_map.get('Product Delete')
    if (api_obj is None):
        frappe.throw('Missing API URL for deleting product. Please check your OC Site\'s settings')
    response = request_oc_url(site_doc.get('server_base_url'), headers, {}, api_obj, url_params={'id': doc.get(OC_PROD_ID)})

    # Parse json
    try:
        response_json = json.loads(response)
    except Exception as e:
        frappe.throw('Response has invalid format %s'%response)

    # Not successful
    if (not response_json.get('success')):
        frappe.msgprint('Product not deleted on Opencart. Error: %s' %(response_json.get('error')))
    else:
        frappe.msgprint('Product successfully deleted on Opencart')

@authenticated_opencart
def oc_validate_item (doc, site_doc, api_map, headers, method=None):
    root_group = site_doc.get('root_item_group')
    valid_groups = [x[0] for x in get_child_groups(root_group)]
    valid_groups.append(root_group)
    # Check if current group is valid
    if (doc.get('item_group') not in valid_groups):
        raise Exception('To be able to sold on selected Ecommerce site, Item Group must be one of the followings: %s'%str(valid_groups))

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
