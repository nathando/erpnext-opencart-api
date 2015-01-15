"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import request_oc_url
from datetime import datetime
import frappe, json, os, traceback
import httplib, urllib

OC_CAT_ID = 'opencart_category_id'


# Validate before saving
@authenticated_opencart
def oc_validate_group (doc, site_doc, api_map, headers, method=None):
    pass

# Insert/Update Item Group (Category)
@authenticated_opencart
def oc_update_group (doc, site_doc, api_map, headers, method=None):
    # Check method
    if method != 'on_update':
        frappe.throw('Unknown method %s'%method)
    is_updating = doc.get(OC_CAT_ID) and doc.get(OC_CAT_ID) > 0
    data = {
        "sort_order": "1",
        "parent_id": "0",
        "status": "1",
        "category_store": ["0"],
        "category_description": {
    		"1":{
    			"name": doc.get('name'),
                "description" : "description",
    			"meta_keyword" : "test category meta_keyword",
                "meta_description" : "test category meta_description",
    		}
    	}
    }

# Delete Item Group (Category)
@authenticated_opencart
def oc_delete_group (doc, site_doc, api_map, headers, method=None):
    pass

# Get child group
@frappe.whitelist()
def get_child_groups(item_group_name):
	item_group = frappe.get_doc("Item Group", item_group_name)
	return frappe.db.sql("""select name, parent_item_group, opencart_category_id, opencart_last_sync
		from `tabItem Group` where lft>%(lft)s and rgt<=%(rgt)s order by lft asc""", {"lft": item_group.lft, "rgt": item_group.rgt})


def get_api_by_name(api_map, name):
    # return next((obj for obj in api_map if obj.get('name')==name), None)
    for obj in api_map:
        if obj.get('api_name') == name:
            return obj
    return None

# Sync children groups
@frappe.whitelist()
def sync_child_groups(item_group_name, site_name, server_base_url, api_map, header_key, header_value):
    item_group = frappe.get_doc("Item Group", item_group_name)
    field_dict = ["name", ]
    filters_dict = [
        ["Item Group", "lft", ">", item_group.lft],
        ["Item Group", "rgt", "<=", item_group.rgt]
    ]
    groups = (frappe.get_list("Item Group", filters=filters_dict, docstatus="1", order_by="lft"))
    #
    results = []
    # Load api map
    api_map = json.loads(api_map)
    # Loop through group and update
    for group in groups:
        group_doc = frappe.get_doc("Item Group", group.get('name'))
        # Parent category
        parent_id = "0"
        if group_doc.get('parent_item_group')!=item_group_name:
            parent_doc = frappe.get_doc("Item Group", group_doc.get('parent_item_group'))
            parent_id = parent_doc.get('opencart_category_id')

        # Header
        headers = {}
        headers[header_key] = header_value

        # Sync with oc
        is_updating = group_doc.get(OC_CAT_ID) and group_doc.get(OC_CAT_ID) > 0
        data = {
            "sort_order": "1",
            "parent_id": parent_id,
            "status": "1",
            "category_store": ["0"],
            "category_description": {
        		"1":{
        			"name": group_doc.get('name'),
                    "description" : "description",
        			"meta_keyword" : "test category meta_keyword",
                    "meta_description" : "test category meta_description",
        		}
        	},
            "keyword": ','.join(["category", group_doc.get('name')]),  # Prevent error from
            "column": "1"
        }

        # Get API obj
        if is_updating:
            api_obj = get_api_by_name(api_map, 'Category Edit')
            api_params = {'id': group_doc.get(OC_CAT_ID)}
        else:
            api_obj = get_api_by_name(api_map, 'Category Add')
            api_params = None

        if (api_obj is None):
            frappe.throw('Missing API URL for adding/updating product')

        # Push change to server
        response = request_oc_url(server_base_url, headers, data, api_obj, url_params = api_params)

        # Parse json
        try:
            response_json = json.loads(response)
        except Exception as e:
            frappe.throw('Response has invalid format %s'%response)

        # Handle response
        if (response_json.get('success')==True):
            group.update({
                "sell_on_opencart": True,
                "opencart_site": site_name,
                "opencart_last_sync": datetime.now()
            })
            if not group_doc.opencart_category_id:
                group.update({"opencart_category_id": response_json.get('category_id')})
            group_doc.update(group)
            group_doc.save()
        results.append([group_doc.get('name'), group_doc.get('parent_item_group'), group_doc.get('opencart_category_id'), group_doc.get_formatted('opencart_last_sync')])
    return results


# Opencart API
# Category {
# category_description (array[CategoryDescription]),
# keyword (string, optional): List of comma separated fields keywords,
# sort_order (integer): Sort order of category,
# category_store (array[integer]): List of stores,
# category_filter (array[integer], optional): List of category filters,
# parent_id (integer): Category parent id,
# column (integer, optional): Number of columns to use for the bottom 3 categories. Only works for the top parent categories.,
# top (integer, optional): Display in the top menu bar. Only works for the top parent categories.,
# status (integer) = ['1-Enabled' or '0-Disabled']: Category status.
# }
# Category description {
# name (string): Name of the category,
# description (string): Description of the category,
# meta_description (string, optional): Meta description of the category,
# meta_keyword (string, optional): Meta keyword of the category
# }
