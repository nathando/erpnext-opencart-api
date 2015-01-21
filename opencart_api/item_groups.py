"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import oc_requests, sync_info
from datetime import datetime, timedelta
from frappe.utils import get_datetime
import frappe, json, os, traceback
import httplib, urllib

OC_CAT_ID = 'opencart_category_id'
OC_CAT_SYNC_BUFFER = 2 #seconds

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
    api_name = 'Category Edit' if is_updating else 'Category Add'
    api_params = {'id': doc.get(OC_CAT_ID)} if is_updating else None

    # Push change to server
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, api_name, \
        url_params = api_params, data=data)
    if res:
        # Check success
        action = 'updated' if is_updating else 'added'
        if (not res.get('success')):
            frappe.msgprint('Category not %s. Error: %s' %(action, res.get('error')))
        else:
            if (not is_updating):
                doc.update({OC_CAT_ID: res.get('category_id')})
            doc.opencart_last_sync= datetime.now()
            frappe.msgprint('Category successfully %s'%action)


# Delete Item Group (Category)
@authenticated_opencart
def oc_delete_group (doc, site_doc, api_map, headers, method=None):
    # Delete are not allow if cannot connect to opencart
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, 'Category Delete', \
            url_params={'id': doc.get(OC_CAT_ID)}, stop=True)
    if res:
        # Not successful
        if (not res.get('success')):
            frappe.msgprint('Category not deleted on Opencart. Error: %s' %(res.get('error')))
        else:
            frappe.msgprint('Category successfully deleted on Opencart')

# Get child group
@frappe.whitelist()
def get_child_groups(item_group_name):
    item_group = frappe.get_doc("Item Group", item_group_name)
    groups = frappe.db.sql("""select name, parent_item_group, opencart_category_id, opencart_last_sync, modified, \
        if(opencart_last_sync + INTERVAL %(buffer)s SECOND > modified, 1, 0) as updated \
        from `tabItem Group` where lft>%(lft)s and rgt<=%(rgt)s order by lft asc""", {"lft": item_group.lft, "rgt": item_group.rgt, "buffer": OC_CAT_SYNC_BUFFER})
    return [group+(("updated", "Updated") if group[5]==1 else ("not-updated", "Not Updated")) for group in groups]

# Manually sync children groups
@frappe.whitelist()
def sync_child_groups(item_group_name, site_name, server_base_url, api_map, header_key, header_value, silent=False):
    #
    item_group = frappe.get_doc("Item Group", item_group_name)
    logs = []
    # Check if any is not updated
    count = frappe.db.sql("""select count(*) from \
        (select if(opencart_last_sync + INTERVAL %(buffer)s SECOND > modified, 1, 0) as updated \
        from `tabItem Group` where lft>%(lft)s and rgt<=%(rgt)s) as cat_tbl where cat_tbl.updated=0""", {"lft": item_group.lft, "rgt": item_group.rgt, "buffer": OC_CAT_SYNC_BUFFER})

    # Init for result
    results = {}
    results_list = []
    update_count = 0
    add_count = 0
    success = True
    # Skip if everything is up to date
    if (count[0][0]==0):
        sync_info(logs, 'All items groups are up to date', stop=True, silent=silent)
    else:
        #
        site_doc = frappe.get_doc("Opencart Site", site_name)
        groups = frappe.db.sql("""select name, if(opencart_last_sync + INTERVAL %(buffer)s SECOND > modified, 1, 0) as updated \
            from `tabItem Group` where lft>%(lft)s and rgt<=%(rgt)s order by lft asc""", {"lft": item_group.lft, "rgt": item_group.rgt, "buffer": OC_CAT_SYNC_BUFFER})
        # Header
        headers = {}
        headers[header_key] = header_value

        # Loop through group and update
        for group in groups:
            group_name, group_updated = group
            group_doc = frappe.get_doc("Item Group", group_name)

            # Check if it synced already 2 sec buffer.
            # Because we save using code the modified get updated after last_sync time
            if (group_updated):
                extras = (1, 'updated', 'Updated')
            else:
                extras = (0, 'not-updated', 'Not Updated')
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
                api_name = 'Category Edit' if is_updating else 'Category Add'
                api_params = {'id': group_doc.get(OC_CAT_ID)} if is_updating else None

                # Push change to server
                res = oc_requests(server_base_url, headers, api_map, api_name, url_params=api_params, data=data, logs=logs, silent=silent, stop=False)
                if res is None or res.get('success')==False:
                    success = False
                    sync_info(logs, "Failed to update/add item group: %s. Error: %s"%(group_name, \
                        res.get('error') if hasattr(res, 'error') else 'Unknown error'), error=True, silent=silent)
                    # Handle response
                else:
                    updating_props = {
                        "sell_on_opencart": True,
                        "opencart_site": site_name,
                        "opencart_last_sync": datetime.now()
                    }
                    if not group_doc.opencart_category_id:
                        updating_props.update({"opencart_category_id": res.get('category_id')})
                    group_doc.update(updating_props)
                    group_doc.ignore_validate=True
                    group_doc.save()
                    # Add count
                    if (is_updating):
                        update_count+=1
                        extras = (group_updated, 'just-updated', 'Just Updated')
                        sync_info(logs, "Successfully updated item group: %s."%(group_name), error=False, silent=True)
                    else:
                        add_count+=1
                        extras = (group_updated, 'just-added', 'Just Added')
                        sync_info(logs, "Successfully added item group: %s."%(group_name), error=False, silent=True)

                # Update images as well, optional
                sync_group_image_handle (group_doc, site_doc, api_map, headers)

            # Append results
            results_list.append((group_doc.get('name'), group_doc.get('parent_item_group'), \
             group_doc.get('opencart_category_id'), group_doc.get_formatted('opencart_last_sync'), \
             group_doc.get('modified'))+extras)

    results = {
        'add_count': add_count,
        'update_count': update_count,
        'results': results_list,
        'success': success,
        'logs': logs
    }
    return results


# Sync item's primary image
def sync_group_image_handle (doc, site_doc, api_map, headers):
    pass
    # # Get API obj
    # api_obj = get_api_by_name(api_map, 'Category Image')
    # if (not api_obj):
    #     return
    #
    # # Check if we have image
    # if (not doc.get('oc_image') or doc.get('oc_image')==''):
    #     return
    #
    # # Let's get the file
    # image_file_data = frappe.get_doc("File Data", {
	# 	"file_url": doc.get('oc_image'),
	# 	"attached_to_doctype": "Item Group",
	# 	"attached_to_name": doc.get('name')
	# })
    # if (image_file_data is None):
    #     return
    #
    # file_path = get_files_path() + '/' + image_file_data.get('file_name')
    #
    # # Push image onto oc server
    # url = 'http://'+site_doc.get('server_base_url') + get_api_url(api_obj, {'id': doc.get(OC_PROD_ID)})
    # try:
    #     response = oc_upload_file(url, headers, {}, file_path)
    #     if (response.status_code!=200):
    #         pass
    #     else:
    #         res = json.loads(response.text)
    #         if (res.get('success')):
    #             doc.last_sync_image = datetime.now()
    #             doc.save()
    #             return doc.last_sync_image
    #         else:
    #             pass
    # except Exception as e:
    #     pass

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
