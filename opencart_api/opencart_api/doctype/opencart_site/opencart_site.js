// Copyright (c) 2015, Hoovix Pvt. Ltd. and Contributors

// Print table log
print_sync_log_cat = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Parent Name</th><th>Opencart Category ID</th><th>Last Sync</th><th>Last Modified</th>');
    var groups = $.map(update ? message.results: message, function(o){
        $tr = $('<tr>');
        // Add class
        if (o[5]) {
            $tr.addClass(o[5]);
        }
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Sync Log: ")+'</h4>');
    $panel.append($header);

    if (update){
        var $info;
        if (message.add_count || message.update_count) {
            $info = $('<p></p>').html('Added ' + message.add_count +' categories, Updated ' + message.update_count + ' categories');
        }
        else {
            $info = $('<p>All item groups are up to date</p>');
        }
        $panel.append($info);
        $panel.append($table);
        var msg = $('<div>').append($panel).html();
        $(cur_frm.fields_dict['group_sync_log'].wrapper).html(msg);
    }
    else {
        $info = $('<p>All item groups are up to date</p>');
        $panel.append($info);
        $panel.append($table);
        var msg = $('<div>').append($panel).html();
        $(cur_frm.fields_dict['group_sync_log'].wrapper).html(msg);
    }
}

//
print_sync_log_item = function(message, update) {
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Item Code</th><th>Item Name</th><th>Opencart Product ID</th><th>Last Sync</th><th>Last Modified</th>');
    var groups = $.map(message.results, function(o){
        $tr = $('<tr>');
        // Add class
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tr.append('<td>'+o[4]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    var $panel = $('<div class="panel"></div>');
    var $header = $('<h4>'+__("Sync Log: ")+'</h4>');
    $panel.append($header);

    if (update){
        var $info;
        if (message.add_count || message.update_count) {
            $info = $('<p></p>').html('Added ' + message.add_count +' items, Updated ' + message.update_count + ' items');
        }
        else {
            $info = $('<p>All item are up to date</p>');
        }
        $panel.append($info);
        $panel.append($table);
        var msg = $('<div>').append($panel).html();
        $(cur_frm.fields_dict['item_sync_log'].wrapper).html(msg);
    }
    else {
        $info = $('<p>All item are up to date</p>');
        $panel.append($info);
        $panel.append($table);
        var msg = $('<div>').append($panel).html();
        $(cur_frm.fields_dict['item_sync_log'].wrapper).html(msg);
    }
}

print_children_group = function(doc, dt, dn) {
    frappe.call({
        type: "GET",
        args: {
            cmd: "opencart_api.item_groups.get_child_groups",
            item_group_name: doc.root_item_group
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_cat(data.message);
            }
        }
    });
}

// Refresh
cur_frm.cscript.refresh = function(doc, dt, dn) {
    // Get all its child group to
    print_children_group(doc, dt, dn);
}

// Handle item root group selected
cur_frm.cscript.root_item_group = function(doc, dt, dn) {
    // Get all its child group to
    print_children_group(doc, dt, dn);
}

// Handle sync categories button pressed
cur_frm.cscript.sync_with_oc_site = function(doc, dt, dn) {
    // TODO: Give some warnings if some categories already has an opencart site
    frappe.call({
        type: "GET",
        args: {
            cmd: "opencart_api.item_groups.sync_child_groups",
            api_map: doc.api_map,
            site_name: doc.name,
            header_key: doc.opencart_header_key,
            header_value: doc.opencart_header_value,
            server_base_url: doc.server_base_url,
            item_group_name: doc.root_item_group
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_cat(data.message, true);
            }
        }
    });
}



// Handle sync categories button pressed
cur_frm.cscript.sync_item_with_oc_site = function(doc, dt, dn) {
    // TODO: Give some warnings if some categories already has an opencart site
    frappe.call({
        type: "GET",
        args: {
            cmd: "opencart_api.items.sync_all_items",
            api_map: doc.api_map,
            site_name: doc.name,
            header_key: doc.opencart_header_key,
            header_value: doc.opencart_header_value,
            server_base_url: doc.server_base_url
        },
        callback: function(data) {
            if (data && data.message) {
                print_sync_log_item(data.message, true);
            }
        }
    });
}
