"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Item/Product related functions
Interfacing with Open Cart API
"""
from decorators import authenticated_opencart
from utils import request_oc_url, oc_upload_file, get_api_by_name
from item_groups import get_child_groups
from datetime import datetime
from frappe.utils import get_files_path, get_path, get_site_path
import frappe, json, os, traceback, base64
from opencart_api.doctype.opencart_api_map_item.opencart_api_map_item import get_api_url

OC_PROD_ID = 'oc_product_id'
OC_CAT_ID = 'opencart_category_id'

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
    qty = get_quantity(doc, is_updating=is_updating)
    data = {
    	"model": doc.get('item_code'),
    	"sku": doc.get('item_code'),
    	"price": doc.get('oc_price'),
    	"status": doc.get('oc_enable'),
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
    api_obj = api_map.get('Product Add')
    api_params = None
    if is_updating:
        api_obj = api_map.get('Product Edit')
        api_params = {'id': doc.get(OC_PROD_ID)}
    if (api_obj is None):
        frappe.msgprint('Missing API URL for adding/updating product. Please sync this with opencart again later')
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
        frappe.msgprint('Product not %s on Opencart. Error: %s' %(action, response_json.get('error')))
    else:
        doc.update({'last_sync_oc': datetime.now()})
        if (not is_updating):
            doc.update({OC_PROD_ID: response_json.get('product_id')})
        frappe.msgprint('Product successfully %s'%action)

@authenticated_opencart
def oc_delete_item (doc, site_doc, api_map, headers, method=None):
    # Push delete on oc server
    api_obj = api_map.get('Product Delete')
    if (api_obj is None):
        frappe.throw('Missing API URL for deleting product. Please check your OC Site\'s settings')
    response = request_oc_url(site_doc.get('server_base_url'), headers, {}, api_obj, url_params={'id': doc.get(OC_PROD_ID)}, throw_error=True)

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

# Sync item's primary image
@authenticated_opencart
def sync_item_image_handle (doc, site_doc, api_map, headers):
    # Get API obj
    api_obj = api_map.get('Product Image')
    if (not api_obj):
        frappe.throw('Missing API URL for adding/updating product\'s image')

    # Check if we have image
    if (not doc.get('image') or doc.get('image')==''):
        frappe.throw('There is no image to sync')
    # Let's get the file
    image_file_data = frappe.get_doc("File Data", {
		"file_url": doc.get('image'),
		"attached_to_doctype": "Item",
		"attached_to_name": doc.get('name')
	})
    if (image_file_data is None):
        frappe.throw('Cannot find image with path %s' %doc.get('image'))

    file_path = get_files_path() + '/' + image_file_data.get('file_name')

    # Push image onto oc server
    url = 'http://'+site_doc.get('server_base_url') + get_api_url(api_obj, {'id': doc.get(OC_PROD_ID)})
    try:
        response = oc_upload_file(url, headers, {}, file_path)
        if (response.status_code!=200):
            frappe.throw('Error occur when posting image to opencart. Status code: %s'%str(response.status_code))
        else:
            res = json.loads(response.text)
            if (res.get('success')):
                doc.update({'last_sync_image': datetime.now()})
                return doc.last_sync_image
            else:
                frappe.throw('Unknown error posting image. Image not updated')
    except Exception as e:
        frappe.throw('Error occur when posting image to opencart. Exception: %s'%str(e))

# Sync item's image
@frappe.whitelist()
def sync_item_image(item_name):
    item_doc = frappe.get_doc("Item", item_name)
    # Double check if the item is just local
    if item_doc is None:
        frappe.throw("Cannot find item with name %s, or item has not been saved" %item_name)
    return sync_item_image_handle(item_doc)

# Manually sync items which belongs to a opencart site
@frappe.whitelist()
def sync_all_items(server_base_url, api_map, header_key, header_value):
    # Get API obj
    api_map = json.loads(api_map)
    api_obj = get_api_by_name(api_map, 'Bulk Product Edit')
    if (api_obj is None):
        frappe.throw('Missing API URL for bulk updating/adding product. Please sync this with opencart again later')
    # Header
    headers = {}
    headers[header_key] = header_value

    # Query for items that has synced time < modified time
    items = frappe.db.sql("""select name, oc_product_id, item_code, item_name, description, \
    oc_meta_keyword, oc_meta_description, oc_price, oc_enable, item_group, modified, last_sync_oc  from `tabItem` where last_sync_oc<modified and oc_product_id is not null""")

    #
    if (len(items)==0):
        frappe.throw('All items are up to date')
    data = []
    names = []
    results = []
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
    response = request_oc_url(server_base_url, headers, data, api_obj)
    if (response is None):
        return
    # Parse json
    try:
        response_json = json.loads(response)
    except Exception as e:
        frappe.msgprint('Response has invalid format %s. Please sync this with opencart again later'%response)
        return

    # Success ?
    success = False
    if (not response_json.get('success')):
        frappe.msgprint('Some product not updated on Opencart. Error: %s' %(response_json.get('error')))
    else:
        frappe.db.sql("""update `tabItem` set last_sync_oc = Now() where name in (%s)""" %(','.join(names)))
        frappe.msgprint('%d Product(s) successfully updated to Opencart site' %len(items))
        success = True
    return {
        'results': results,
        'success': success
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
