"""
Author: Nathan Do
Email: nathan.dole@gmail.com
"""
import frappe, json, os, traceback

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

def opencart_api(fn):
    def opencart_fn(*args, **kw):
        user = frappe.local.session.get('user', "Guest")
        # Get the opencart config
        config = frappe.local.db.get_singles_dict('Opencart Config')

        # Select the site that associated with this user
        sites = frappe.get_list("Opencart Site", filters={'user': user})
        if len(sites)==0:
            return {"status": -1, "error": "Cannot find a matched site with this user: %s" %user}
        # Get the site doc - Only the first one associated with this username considered
        site_doc = frappe.get_doc('Opencart Site', sites[0])
        try:
            return fn(config, site_doc, *args, **kw)
        except frappe.PermissionError as e:
            error_status = kw.get('error_status', -1)
            return {"status": error_status, "error": "Permission Error: " +  str(e)}
        except Exception as e:
            return {"status": -10, "error": str(e), "traceback": traceback.format_exc()}
    return opencart_fn
