"""
Author: Nathan Do
Email: nathan.dole@gmail.com
"""
import frappe, json, os, traceback, urllib2
from decorators import get_only, post_only, authenticated_api, opencart_api
# =========== Login API =============
# Params:
# 1. usr: username
# 2. pwd: password
# Return:
# 1. status: -1=Failure, 1=Success
# 2. error: Error message only available if status -1
@frappe.whitelist(allow_guest=True)
@post_only
def login():
    try:
        frappe.local.login_manager.login()
        full_name = frappe.response.pop("full_name")
        return {"status": 1, "full_name": full_name}
    except frappe.AuthenticationError:
        return {"status": -1, "error": "Authentication failed"}

# =========== Logout API =============
@frappe.whitelist(allow_guest=True)
def logout():
    try:
        frappe.local.login_manager.logout()
        return {"status": 1}
    except:
        return {"status": -1, "error": "Unexpected error occur"}

# ============ Categories ===============
def get_groups_recursive(parent_item_group, flat=False):
    filters_dict = {'parent_item_group': parent_item_group}
    # Select columns to return
    fields = ["name", "modified", "is_group"]
    # Get data
    data = frappe.get_list("Item Group", filters=filters_dict, fields=fields)
    # Loop and get recursion
    extra = []
    for item in data:
        item.is_group = True if item.get('is_group').lower() == 'yes' else False
        item.parent = parent_item_group
        if (item.get('is_group')):
            if flat:
                extra = (get_groups_recursive(item.get('name')))
            else:
                item.children = get_groups_recursive(item.get('name'))
    data += extra
    return data


@frappe.whitelist(allow_guest=True)
@authenticated_api
@get_only
@opencart_api
def get_item_group_list(config, site_doc):
    ''' Get all item groups to sync with Opencart DB '''
    # Get the root item group
    parent_item_group = site_doc.get('root_item_group', config.get('default_item_group'))
    flat = frappe.local.form_dict.get('flat', False)
    # Filter by root group
    data = get_groups_recursive(parent_item_group, flat=flat)
    return data


@frappe.whitelist(allow_guest=True)
@authenticated_api
@get_only
@opencart_api
def add_item_group(config, site_doc):
    ''' Add an item group (Opencart Category) '''
    # Name is compulsory
    name = frappe.local.form_dict.get('name')
    if name is None:
        return {"status": -1, "error": "Missing compulsory parameter 'name'"}

    # Is group ?
    is_group = frappe.local.form_dict.get('is_group', True)
    is_group = 'Yes' if is_group else 'No'

    # Maybe add description ?

    # Parent
    user_root_item_group = site_doc.get('root_item_group', config.get('default_item_group'))
    parent_item_group = frappe.local.form_dict.get('parent_name', user_root_item_group)

    # Check if parent supposed to have children
    parent_doc = frappe.get_doc('Item Group', parent_item_group)
    if (parent_doc.get('is_group')=='No'):
        return {"status": -1, "error": "Cannot add Item group. The parent group '%s' does not allow subgroup" %parent_item_group}

    # Add new group
    try:
        new_doc = frappe.new_doc('Item Group')
        new_doc.update({
            'item_group_name': name,
            'parent_item_group': parent_item_group,
            'is_group': is_group,
            'name': name
        })
        new_doc.save()
        return {"status": 1, 'message': 'Successfully added New Item Group %s' %name}
    except Exception as e:
        return {"status": -2, "error": "Cannot insert new Item Group. %s" %str(e)}


@frappe.whitelist(allow_guest=True)
@authenticated_api
@get_only
@opencart_api
def update_item_group(config, site_doc):
    ''' Update an item group (Opencart Category) '''
    # Name is compulsory
    name = frappe.local.form_dict.get('name')
    if name is None:
        return {"status": -1, "error": "Missing compulsory parameter 'name'"}

    #
    try:
        group_doc = frappe.get_doc('Item Group', name)
    except Exception as e:
        return {"status": -1, "error": "Item Group with name: '%s' does not exist" %name}

    # Update
    try:
        if frappe.local.form_dict.get('parent_item_group'):
            group_doc.update({'parent_item_group': frappe.local.form_dict.get('parent_item_group')})
        if frappe.local.form_dict.get('is_group'):
            group_doc.update({'is_group': 'Yes' if frappe.local.form_dict.get('is_group') else 'No' })

        group_doc.save()
        return {"status": 1, 'message': 'Successfully updated Item Group %s' %name}
    except Exception as e:
        return {"status": -2, "error": "Cannot update Item Group. %s" %str(e)}


# ============ Items/Product ===============
@frappe.whitelist(allow_guest=True)
@authenticated_api
@get_only
@opencart_api
def get_items(config, site_doc):
    ''' Get all items are root group and its descendant. Sync with Opencart DB '''
    # Select columns to return
    fields = ["name", "item_code", "item_group"]
    # Get filters
    filters = []
    accepted_filters = {'name': 'name', 'sku': 'item_code', 'category': 'item_group'}
    for open_field, erp_field in accepted_filters.iteritems():
        if (frappe.local.form_dict.get(open_field)):
            filters.append(["Item", erp_field, "=", frappe.local.form_dict.get(open_field)])

    # Should we limit to only root group ?
    parent_item_group = site_doc.get('root_item_group', config.get('default_item_group'))
    groups = get_groups_recursive(parent_item_group, flat=True)
    group_names = map(lambda x: x.get('name'), groups)
    group_names.append(parent_item_group)

    if len(group_names)>0:
        filters.append(["Item", 'item_group', 'in', group_names])
    # Return data
    data = frappe.get_list('Item', filters=filters, fields=fields)
    return data
