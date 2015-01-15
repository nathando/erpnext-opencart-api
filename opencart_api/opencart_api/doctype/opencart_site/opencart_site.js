// Copyright (c) 2015, Hoovix Pvt. Ltd. and Contributors

// Print to log
print_group_log = function(msg) {
    $(cur_frm.fields_dict['group_sync_log'].wrapper).html('<div class="panel"><h4>'+__("Sync Log:")+'</h4><div>'+msg+'</div></div>');
}

// Print table log
print_sync_log = function(message) {
    console.log(message);
    var $table = $('<table class="table table-bordered"></table>');
    var $th = $('<tr></tr>');
    var $tbody = $('<tbody></tbody>');
    $th.html('<th>Name</th><th>Parent Name</th><th>Opencart Category ID</th><th>Last Sync</th>');
    var groups = $.map(message, function(o){
        $tr = $('<tr>');
        $tr.append('<td>'+o[0]+'</td>');
        $tr.append('<td>'+o[1]+'</td>');
        $tr.append('<td>'+o[2]+'</td>');
        $tr.append('<td>'+o[3]+'</td>');
        $tbody.append($tr);
    });
    $table.append($th).append($tbody);
    print_group_log($('<div>').append($table).html());
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
                print_sync_log(data.message);
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
                print_sync_log(data.message);
            }
        }
    });
}
