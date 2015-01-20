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

def oc_requests(server_base_url, headers, api_map, api_name, url_params=None, file_path=None, throw_error=False, data=None):
    try:
        # Validate
        if isinstance(api_map, basestring):
            api_map = json.loads(api_map)
            api_obj = get_api_by_name(api_map, api_name)
        else:
            api_obj = api_map.get(api_name)
        if (api_obj is None):
            frappe.msgprint('Missing API URL: %s. Please sync this with opencart again later')
            return None

        # Get url and method from API Map
        url = (server_base_url + ("" if server_base_url.endswith("/") else "") + get_api_url(api_obj, url_params))
        method = api_obj.get('api_method')

        # If data is not dict, encode it to string
        if data is not None:
            data = json.dumps(data)

        # Read files
        files = {'file': open(file_path, 'rb')} if file_path else None

        # Requests
        if (method.lower()=="get"):
            response = requests.get(url, headers=headers, data=data)
        elif (method.lower()=="post"):
            response = requests.post(url, files=files, headers=headers, data=data)
        elif (method.lower()=="put"):
            response = requests.put(url, headers=headers, data=data)
        elif (method.lower()=="delete"):
            response = requests.delete(url, headers=headers, data=data)
        #
        if (response is None or response.status_code!=200):
            frappe.msgprint('Error occur when posting image to opencart. Status code: %s'%str(response.status_code))
        else:
            # Parse json
            try:
                return json.loads(response.text)
            except Exception as e:
                frappe.msgprint('Response has invalid format %s. Please sync this with opencart again later'%response)
        return None

    except Exception as e:
        if (throw_error):
            frappe.throw('Error occured: %s. Please sync this with opencart again later' % str(e))
        else:
            frappe.msgprint('Error occured: %s. Please sync this with opencart again later' % str(e))
        frappe.get_logger().error("Unexpected exception: " +  str(e) + '. Traceback: ' + traceback.format_exc())

def oc_upload_file(url, headers, data, file_path):
    files = {'file': open(file_path, 'rb')}
    return requests.post(url, files=files, headers=headers, data=data)
