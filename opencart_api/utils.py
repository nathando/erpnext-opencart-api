"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Utils for Opencart API app
"""
import frappe, json, os, traceback, requests
import httplib, urllib
from opencart_api.doctype.opencart_api_map_item.opencart_api_map_item import get_api_url

def get_api_by_name(api_map, name):
    # return next((obj for obj in api_map if obj.get('name')==name), None)
    for obj in api_map:
        if obj.get('api_name') == name:
            return obj
    return None

# Construct the URL and get/post/put
def request_oc_url (server_base_url, headers, data, api_obj, url_params=None, throw_error=False):
    # Create new connection
    try:
        conn = httplib.HTTPConnection(server_base_url)
        # Add Headers
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"

        # Encode data from a dict
        data = json.dumps(data)

        # Get url and method from API Map
        url = get_api_url(api_obj, url_params)
        method = api_obj.get('api_method')

        # Request
        conn.request(method, url, data, headers)
        resp = conn.getresponse()

        # Read response
        content = resp.read()
        conn.close()

        return content

    except Exception as e:
        if (throw_error):
            frappe.throw('Error occured: %s. Please sync this with opencart again later' % str(e))
        else:
            frappe.msgprint('Error occured: %s. Please sync this with opencart again later' % str(e))
        frappe.get_logger().error("Unexpected exception: " +  str(e) + '. Traceback: ' + traceback.format_exc())

def oc_upload_file(url, headers, data, file_path):
    files = {'file': open(file_path, 'rb')}
    return requests.post(url, files=files, headers=headers, data=data)
