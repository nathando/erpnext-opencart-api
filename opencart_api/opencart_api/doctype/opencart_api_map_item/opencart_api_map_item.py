# Copyright (c) 2013, Nathan (Hoovix Consulting Pte. Ltd.) and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class OpencartAPIMapItem(Document):
	pass

def get_api_url(obj, url_params=None):
	url = obj.get('api_url')
	if (url_params is not None):
		url = url.format(**url_params)
	return url
