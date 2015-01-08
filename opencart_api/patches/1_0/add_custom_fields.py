'''
Author: Nathan Do
Email: nathan.dole@gmail.com
Description: Patch to add custom field for Opencart App
'''
from __future__ import unicode_literals
import frappe
from frappe.core.doctype.custom_field.custom_field import create_custom_field

def execute():
    opencart_extra_fields = {
        "Item": [{
            "label": "Opencart Settings",
            "fieldname": "opencart_settings",
            "fieldtype": "Section Break",
            "insert_after": "add_image",
            "permlevel": 1
        },
        {
			"label": "Sell on Opencart",
			"fieldname": "sell_on_opencart",
			"fieldtype": "Check",
            "default": 0,
			"insert_after": "opencart_settings",
			"permlevel": 1
		},
        {
			"label": "Opencart Site",
			"fieldname": "opencart_site",
			"fieldtype": "Link",
            "options": "Opencart Site",
            "depends_on": "eval:doc.sell_on_opencart=='1'",
			"insert_after": "opencart_settings",
			"permlevel": 1
		},
        {
			"label": "Opencart Column Break",
			"fieldname": "oc_cb",
			"fieldtype": "Column Break",
			"insert_after": "opencart_site",
			"permlevel": 1
		},
        {
			"label": "Enable on Opencart",
			"fieldname": "oc_enable",
			"fieldtype": "Check",
            "default": 1,
            "depends_on": "eval:doc.sell_on_opencart=='1'",
			"insert_after": "oc_cb",
			"permlevel": 1
		},
        {
            "label": "Opencart Product ID",
            "fieldname": "oc_product_id",
            "fieldtype": "Data",
            "depends_on": "eval:doc.sell_on_opencart=='1'",
            "read_only": 1,
			"insert_after": "oc_enable",
			"permlevel": 1
        }]
    }
    for dt, docfields in opencart_extra_fields.items():
        for df in docfields:
            df = frappe._dict(df)
            create_custom_field(dt, df)
