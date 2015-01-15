"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Utils for Opencart API app
"""
import frappe, json, os, traceback
import httplib, urllib

# Construct the URL and get/post/put
def request_oc_url (server_base_url, headers, data, api_obj, url_params=None):
    # Create new connection
    try:
        conn = httplib.HTTPConnection(server_base_url)
        # Add Headers
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"

        # Encode data from a dict
        data = json.dumps(data)

        # Get url and method from API Map
        url = api_obj.get('api_url')
        if (url_params is not None):
            url = url.format(**url_params)
        method = api_obj.get('api_method')

        # Request
        conn.request(method, url, data, headers)
        resp = conn.getresponse()

        # Read response
        content = resp.read()
        conn.close()

        return content

    except Exception as e:
        frappe.throw('Error occured: ' + str(e))
        frappe.get_logger().error("Unexpected exception: " +  str(e) + '. Traceback: ' + traceback.format_exc())
