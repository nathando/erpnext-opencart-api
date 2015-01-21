"""
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Utils for Opencart API app
"""
import frappe, json, os, traceback, requests
import httplib, urllib
from datetime import datetime
from opencart_api.doctype.opencart_api_map_item.opencart_api_map_item import get_api_url

# Sync Log format
def sync_log_create(error, message):
    return "[%s] %s: %s"%(datetime.now().strftime("%d-%b-%y %H:%M:%S"), "ERR" if error else "INF", message)

# Report sync error/info, depend on whether silent flag is set
def sync_info(logs, message, error=False, stop=False, silent=False):
    logs.append(sync_log_create(error, message))
    # Show ui
    if not silent:
        prompt_fn = frappe.throw if stop else frappe.msgprint
        prompt_fn(message)

# Retrieve the api object from api map list
def get_api_by_name(api_map, name):
    # return next((obj for obj in api_map if obj.get('name')==name), None)
    for obj in api_map:
        if obj.get('api_name') == name:
            return obj
    return None

# Handle all request to oc
def oc_requests(server_base_url, headers, api_map, api_name, url_params=None, file_path=None, stop=False, silent=False, logs=[], data=None):
    try:
        # Validate
        if isinstance(api_map, basestring):
            api_map = json.loads(api_map)

        if isinstance(api_map, dict):
            api_obj = api_map.get(api_name)
        elif isinstance(api_map, list):
            api_obj = get_api_by_name(api_map, api_name)

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
                sync_info(logs, 'Response has invalid format %s. Please sync this with opencart again later!'%response, stop=stop, silent=silent, error=True)

    except requests.ConnectionError:
        sync_info(logs, 'Cannot connect to Opencart Site. Please sync this with opencart again later!', stop=stop, silent=silent, error=True)
    except Exception as e:
        sync_info(logs, 'Unknown error: %s. Please sync this with opencart again later!'%str(e), stop=stop, silent=silent, error=True)
    return None

def oc_upload_file(url, headers, data, file_path):
    files = {'file': open(file_path, 'rb')}
    return requests.post(url, files=files, headers=headers, data=data)
