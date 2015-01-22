"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import oc_requests, sync_info
from item_groups import get_child_groups
from item_qty import get_item_qty
from datetime import datetime
from frappe.utils import get_files_path, flt, cint
import frappe, json, os, traceback, base64
from opencart_api.doctype.opencart_api_map_item.opencart_api_map_item import get_api_url

OC_PROD_ID = 'oc_product_id'
OC_CAT_ID = 'opencart_category_id'

# Insert/Update Item
@authenticated_opencart
def oc_validate_item (doc, site_doc, api_map, headers, method=None):
    # Get the group
    product_categories = []
    root_group = site_doc.get('root_item_group')
    if (doc.get('item_group') == root_group):
        product_categories.append(0)
    else:
        # Check valid group
        valid_groups = [x[0] for x in get_child_groups(root_group)]
        valid_groups.append(root_group)

        # Check if current group is valid
        if (doc.get('item_group') not in valid_groups):
            raise Exception('To be able to sold on selected Ecommerce site, Item Group must be one of the followings: %s'%str(valid_groups))
        # Check if the group already synced first time
        item_group = frappe.get_doc("Item Group", doc.get('item_group'))
        if (not item_group.get(OC_CAT_ID)):
            raise Exception('Category you selected has not been synced to opencart. Please do a manual sync <a href="%s">here</a> '%str(site_doc.get_url()))
        product_categories.append(item_group.get(OC_CAT_ID))

    # Pass validation
    is_updating = doc.get(OC_PROD_ID) and doc.get(OC_PROD_ID) > 0

    # Get quantity
    qty = get_item_qty(doc)
    data = {
    	"model": doc.get('item_code'),
    	"sku": doc.get('item_code'),
    	"price": doc.get('oc_price'),
    	"status": doc.get('oc_enable'),
        "quantity": str(cint(qty)),
        "product_store": ["0"],
        "product_category": product_categories,
        "product_description": {
    		"1":{
    			"name": doc.get('item_name'),
    			"meta_keyword" : doc.get('oc_meta_keyword') or '',
                "meta_description" : doc.get('oc_meta_description') or '',
    			"description" : doc.get('description') or ''
    		}
    	},
        # Irrelevant
        "sort_order": "1",
    	"tax_class_id": "1",
    	"manufacturer_id": "1"
    }
    # Get API obj
    api_name = 'Product Edit' if is_updating else 'Product Add'
    api_params = {'id': doc.get(OC_PROD_ID)} if is_updating else None

    # Push change to server
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, api_name, data=data, url_params = api_params)
    if res:
        # Check success
        action = 'updated' if is_updating else 'added'
        if (not res.get('success')):
            frappe.msgprint('Product not %s on Opencart. Error: %s' %(action, res.get('error')))
        else:
            doc.update({'last_sync_oc': datetime.now()})
            if (not is_updating):
                doc.update({OC_PROD_ID: res.get('product_id')})
            frappe.msgprint('Product successfully %s on Opencart'%action)


# Delete real time with opencart
@authenticated_opencart
def oc_delete_item (doc, site_doc, api_map, headers, method=None):
    # Push delete on oc server
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, 'Product Delete', url_params={'id': doc.get(OC_PROD_ID)}, stop=True)
    if res:
        # Not successful
        if (not res.get('success')):
            frappe.msgprint('Product not deleted on Opencart. Error: %s' %(res.get('error')))
        else:
            frappe.msgprint('Product successfully deleted on Opencart')

# Sync item's primary image
@authenticated_opencart
def sync_item_image_handle (doc, site_doc, api_map, headers, image_path=None):
    # Check if we have image
    if (not image_path or image_path==''):
        frappe.throw('There is no image to sync')

    # Let's get the file
    image_file_data = frappe.get_doc("File Data", {
		"file_url": image_path,
		"attached_to_doctype": "Item",
		"attached_to_name": doc.get('name')
	})
    if (image_file_data is None):
        frappe.throw('Cannot find image with path %s' %image_path)
    file_path = get_files_path() + '/' + image_file_data.get('file_name')

    # Push image onto oc server
    res = oc_requests(site_doc.get('server_base_url'), headers, api_map, 'Product Image', \
        file_path=file_path, url_params={'id': doc.get(OC_PROD_ID)}, throw_error=True)
    if res:
        if (res.get('success')):
            doc.update({'last_sync_image': datetime.now()})
            frappe.msgprint('Successfully updated product\'s image on Opencart')
            return doc.last_sync_image
        else:
            frappe.throw('Unknown error posting image. Image not updated %s' %json.dumps(res))

# Sync item's image
@frappe.whitelist()
def sync_item_image(item_name, image_path):
    item_doc = frappe.get_doc("Item", item_name)
    # Double check if the item is just local
    if item_doc is None:
        frappe.throw("Cannot find item with name %s, or item has not been saved" %item_name)
    return sync_item_image_handle(item_doc, image_path=image_path)

# Manually sync items which belongs to a opencart site
@frappe.whitelist()
def sync_all_items(server_base_url, api_map, header_key, header_value, silent=False):
    # Header
    headers = {}
    headers[header_key] = header_value

    # Query for items that has synced time < modified time
    items = frappe.db.sql("""select name, oc_product_id, item_code, item_name, description, \
    oc_meta_keyword, oc_meta_description, oc_price, oc_enable, item_group, modified, last_sync_oc from `tabItem` where last_sync_oc<modified and oc_product_id is not null""")

    # Init results
    results = []
    logs = []
    success = False
    if (len(items)==0):
        sync_info(logs, 'All items are up to date', stop=True, silent=silent)
    else:
        data = []
        names = []
        for item in items:
            names.append("'"+item[0]+"'")
            data.append ({
                "product_id": item[1],
            	"model": item[2],
            	"sku": item[2],
            	"price": item[7] or 0,
            	"status": item[8],
                "product_store": ["0"],
                "product_category": [item[9]],
                "product_description": {
            		"1":{
            			"name": item[3],
            			"meta_keyword" : item[5] or '',
                        "meta_description" : item[6] or '',
            			"description" : item[4] or ''
            		}
            	},
                # Irrelevant
                "sort_order": "1",
            	"tax_class_id": "1",
            	"manufacturer_id": "1"
            })
            results.append([item[2], item[3], item[1], item[10], item[11]])
        # Bulk Update to server
        res = oc_requests(server_base_url, headers, api_map, 'Bulk Product Edit', data=data, stop=False, logs=logs, silent=silent)
        if res:
            # Success ?
            if (not res.get('success')):
                sync_info(logs, 'Some product not updated on Opencart. Error: %s' %(res.get('error')), stop=False, silent=silent)
            else:
                frappe.db.sql("""update `tabItem` set last_sync_oc = Now() where name in (%s)""" %(','.join(names)))
                sync_info(logs, '%d Product(s) successfully updated to Opencart site' %len(items), stop=False, silent=silent)
                success = True
    return {
        'results': results,
        'success': success,
        'logs': logs
    }

# OC fields
# product_description (array[ProductDescription], optional),
# model (string): Product model,
# sku (string, optional): Stock Keeping Unit,
# quantity (integer): Quantity, - changed to optional
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
