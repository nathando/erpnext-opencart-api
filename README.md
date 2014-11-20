## ERPNext Opencart API

### Warning: This plugin is currently under development. Please do not use it for production now

### Purpose
ERPNext app that aims to connect ERPNext with Opencart through building REST API Endpoints for Opencart to consume. There will be another component for Opencart as well to actually import data.

**Objectives:**  
* Sync as Items and Categories Periodically from ERPNext to Opencart  
* Add a Sales Order when a purchase made in Opencart  
* Add/Update a Order Status for ERPNext's Sales Order (such as 'Ready to ship', 'Shipping', 'Received'). This should be reflected on Opencart administrator.
* Tight up all other related phases of the 2 system like Delivery Order and Sales Invoice (Accounts).

### Preparation
ERPNext is a pretty robust system that can handle multiple ecommerce's data. Therefore, to reduce confusion, this plugin will try to separate those by User/Company/Item Group


### Installation
Following instructions [here](https://github.com/frappe/bench) to install Frappe and ERPNext  
In your shell, run:

```
bench get-app opencart_api https://github.com/nathando/erpnext-opencart-api.git
```
App will create 2 extra **DocTypes**: Opencart Config and Opencart Site  
There are some more preparation steps before trying:

* Create one Item Group which will be the root for all Ecommerce sites (Let's say 'Opencart'). 
* Set this to be the Default Item Group in Opencart Config
* Create a Role and named it **'Opencart Admin'**, and grant this role Permission to **Item**, **Item Group List** (Read, Write, Create Delete)
* Create your Opencart Site's info by going to **Opencart Site** List
* This app assumes that you should have one **User** and one only tight to each **Opencart Site**

### License
MIT License
