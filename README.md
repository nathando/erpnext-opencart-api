## ERPNext Opencart API

### Warning: This plugin is currently under development. Please do not use it for production now

### Purpose
ERPNext app that aims to connect ERPNext with Opencart through building REST API Endpoints for Opencart to consume. There will be another component for Opencart as well to actually import data.

**Objectives:**  
* Sync as Items and Categories Periodically from ERPNext to Opencart  
* Add a Sales Order when a purchase made in Opencart  
* Add/Update a Order Status for ERPNext's Sales Order (such as 'Ready to ship', 'Shipping', 'Received'). This should be reflected on Opencart administrator.
* Tight up all other related phases of the 2 system like Delivery Order and Sales Invoice (Accounts).

### Installation
Following instructions [here](https://github.com/frappe/bench) to install Frappe and ERPNext  
In your shell, run:
`bench get-app opencart_api https://github.com/nathando/erpnext-opencart-api.git`

### License
MIT License
