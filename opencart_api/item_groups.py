"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import request_oc_url, get_api_by_name
from datetime import datetime, timedelta
from frappe.utils import get_datetime
import frappe, json, os, traceback
import httplib, urllib

OC_CAT_ID = 'opencart_category_id'

# Insert/Update Item Group (Category) real time when updating on form
@authenticated_opencart
def oc_validate_group (doc, site_doc, api_map, headers, method=None):
    # Update is allowed even when opencart is down
    is_updating = doc.get(OC_CAT_ID) and doc.get(OC_CAT_ID) > 0
    data = {
        "sort_order": "1",
        "parent_id": "0",
        "status": doc.get('enable_on_opencart'),
        "category_store": ["0"],
        "category_description": {
    		"1":{
    			"name": doc.get('name'),
                "description" : doc.get('opencart_description') or "",
    			"meta_keyword" : doc.get('opencart_meta_keyword') or "",
                "meta_description" : doc.get('opencart_meta_description') or "",
    		}
    	},
        "keyword": ','.join(["category", doc.get('name')]),
        "column": "1"
    }
    # Get API obj
    api_obj = api_map.get('Category Add')
    api_params = None
    if is_updating:
        api_obj = api_map.get('Category Edit')
        api_params = {'id': doc.get(OC_CAT_ID)}
    if (api_obj is None):
        frappe.msgprint('Missing API URL for adding/updating category. Please sync this with opencart again later')
        return

    # Push change to server
    response = request_oc_url(site_doc.get('server_base_url'), headers, data, api_obj, url_params = api_params)
    if (response is None):
        return
    # Parse json
    try:
        response_json = json.loads(response)
    except Exception as e:
        frappe.msgprint('Response has invalid format %s. Please sync this with opencart again later'%response)
        return

    # Check success
    action = 'updated' if is_updating else 'added'
    if (not response_json.get('success')):
        frappe.msgprint('Category not %s. Error: %s' %(action, response_json.get('error')))
    else:
        if (not is_updating):
            doc.update({OC_CAT_ID: response_json.get('category_id')})
        doc.opencart_last_sync= datetime.now()
        frappe.msgprint('Category successfully %s'%action)


# Delete Item Group (Category)
@authenticated_opencart
def oc_delete_group (doc, site_doc, api_map, headers, method=None):
    # Delete are not allow if cannot connect to opencart
    # Push delete on oc server
    api_obj = api_map.get('Category Delete')
    if (api_obj is None):
        frappe.throw('Missing API URL for deleting category. Please check your OC Site\'s settings')
    response = request_oc_url(site_doc.get('server_base_url'), headers, {}, api_obj, url_params={'id': doc.get(OC_CAT_ID)}, throw_error=True)
    if (response is None):
        return
    # Parse json
    try:
        response_json = json.loads(response)
    except Exception as e:
        frappe.throw('Response has invalid format %s. Please sync this with opencart again later'%response)

    # Not successful
    if (not response_json.get('success')):
        frappe.msgprint('Category not deleted on Opencart. Error: %s' %(response_json.get('error')))
    else:
        frappe.msgprint('Category successfully deleted on Opencart')

# Get child group
@frappe.whitelist()
def get_child_groups(item_group_name):
    item_group = frappe.get_doc("Item Group", item_group_name)
    return frappe.db.sql("""select name, parent_item_group, opencart_category_id, opencart_last_sync, modified from `tabItem Group` where lft>%(lft)s and rgt<=%(rgt)s order by lft asc""", {"lft": item_group.lft, "rgt": item_group.rgt})

# Manually sync children groups
@frappe.whitelist()
def sync_child_groups(item_group_name, site_name, server_base_url, api_map, header_key, header_value):
    item_group = frappe.get_doc("Item Group", item_group_name)
    site_doc = frappe.get_doc("Opencart Site", site_name)
    field_dict = ["name", ]
    filters_dict = [
        ["Item Group", "lft", ">", item_group.lft],
        ["Item Group", "rgt", "<=", item_group.rgt]
    ]
    groups = (frappe.get_list("Item Group", filters=filters_dict, docstatus="1", order_by="lft"))
    #
    results = {}
    results_list = []
    # Header
    headers = {}
    headers[header_key] = header_value
    # Load api map
    api_map = json.loads(api_map)
    update_count = 0
    add_count = 0
    # Loop through group and update
    for group in groups:
        group_doc = frappe.get_doc("Item Group", group.get('name'))
        extra_cls = ""
        # Check if it synced already 2 sec buffer
        if (not group_doc.get('opencart_last_sync') or get_datetime(group_doc.get('modified')) > get_datetime(group_doc.get('opencart_last_sync'))+ timedelta(0,2)):
            # Parent category
            parent_id = "0"
            if group_doc.get('parent_item_group')!=item_group_name:
                parent_doc = frappe.get_doc("Item Group", group_doc.get('parent_item_group'))
                parent_id = parent_doc.get('opencart_category_id')

            # Sync with oc
            is_updating = group_doc.get(OC_CAT_ID) and group_doc.get(OC_CAT_ID) > 0
            data = {
                "sort_order": "1",
                "parent_id": parent_id,
                "status": group_doc.get('enable_on_opencart'),
                "category_store": ["0"],
                "category_description": {
            		"1":{
            			"name": group_doc.get('name'),
                        "description" : group_doc.get('opencart_description') or "",
            			"meta_keyword" : group_doc.get('opencart_meta_keyword') or "",
                        "meta_description" : group_doc.get('opencart_meta_description') or "",
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
                group_doc.ignore_validate=True
                group_doc.save()
                # Add count
                if (is_updating):
                    update_count+=1
                    extra_cls = 'just-updated'
                else:
                    add_count+=1
                    extra_cls = 'just-added'
            # Update images as well, optional
            sync_group_image_handle (group_doc, site_doc, api_map, headers)

        # Append results
        results_list.append([group_doc.get('name'), group_doc.get('parent_item_group'), \
         group_doc.get('opencart_category_id'), group_doc.get_formatted('opencart_last_sync'), \
         group_doc.get('modified'), extra_cls])

    results = {
        'add_count': add_count,
        'update_count': update_count,
        'results': results_list
    }
    return results


# Sync item's primary image
def sync_group_image_handle (doc, site_doc, api_map, headers):
    # Get API obj
    api_obj = get_api_by_name(api_map, 'Category Image')
    if (not api_obj):
        return

    # Check if we have image
    if (not doc.get('oc_image') or doc.get('oc_image')==''):
        return

    # Let's get the file
    image_file_data = frappe.get_doc("File Data", {
		"file_url": doc.get('oc_image'),
		"attached_to_doctype": "Item Group",
		"attached_to_name": doc.get('name')
	})
    if (image_file_data is None):
        return

    file_path = get_files_path() + '/' + image_file_data.get('file_name')

    # Push image onto oc server
    url = 'http://'+site_doc.get('server_base_url') + get_api_url(api_obj, {'id': doc.get(OC_PROD_ID)})
    try:
        response = oc_upload_file(url, headers, {}, file_path)
        if (response.status_code!=200):
            pass
        else:
            res = json.loads(response.text)
            if (res.get('success')):
                doc.last_sync_image = datetime.now()
                doc.save()
                return doc.last_sync_image
            else:
                pass
    except Exception as e:
        pass

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
