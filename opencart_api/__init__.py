"""
Author: Nathan Do
Email: nathan.dole@gmail.com
"""
import frappe, json, os, traceback

# ============ Decorators ================
def post_only(fn):
    def create_fn():
        if frappe.local.request.method=="POST":
            return fn()
        else:
            return {"status": -1, "error": "GET method is not allowed"}
    return create_fn

def get_only(fn):
    def create_fn():
        if frappe.local.request.method=="GET":
            return fn()
        else:
            return {"status": -1, "error": "POST method is not allowed"}
    return create_fn

def authenticated_api(fn):
    def auth_fn(*args, **kw):
        if frappe.local.session.get('user', "Guest")=="Guest":
            return {'status':-1, 'error': 'Permission error, you are not allowed to access this resource'}
        else:
            try:
                return fn(*args, **kw)
            except frappe.PermissionError as e:
                error_status = kw.get('error_status', -1)
                return {"status": error_status, "error": "Permission Error: " +  str(e)}
            except Exception as e:

                return {"status": -10, "error": str(e), "traceback": traceback.format_exc()}
    return auth_fn

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
@frappe.whitelist(allow_guest=True)
@authenticated_api
@get_only
def get_item_group_list():
    user = frappe.local.session.get('user', "Guest")
    # Get the opencart config
    config = frappe.local.db.get_singles_dict('Opencart Config')
    # Select the site that associated with this user
    sites = frappe.get_list("Opencart Site", filters={'user': user})
    if len(sites)==0:
        return {"status": -1, "error": "Cannot find a matched site with this user: %s" %user}
    # Get the site doc - Only the first one associated with this username considered
    site_doc = frappe.get_doc('Opencart Site', sites[0])

    # Get the root item group
    parent_item_group = site_doc.get('root_item_group', config.get('default_item_group'))
    # Filter by root group
    filters_dict = {'parent_item_group': parent_item_group}
    # Select columns to return
    fields_dict = ["name"]
    # Get data
    data = frappe.get_list("Item Group", filters=filters_dict, fields=fields_dict)
    return data
