function initializeUI(){
    clearDemos();
}

function clearDemos(){
    $('#demo_list_div').html('');
    $('#demo_client_session_div').html('');
    $('#demo_title').html('');
    $('#demo_title_divider').html('');
    $("#demo_subtitle_divider").html('');
    $("#demo_documentation").html('');
    $('#demo_client_session_div').html('');
    $('#demo_client_inputs').html('');
}

function getDemos(){
    clearDemos();
    $.ajax({
        type : "GET",
        url : $SCRIPT_ROOT + "/request_demo_list",
        contentType : "application/json",
        success : function(data) {
            console.log("Requested Demo List: ", data);
                var demo_list = $('<table id="demo_list" align="center" width="85%" class="spacedTable">')
                $('#demo_list_div').html('') // this resets anything already in the div
                demo_list.append(
                    $('<tr>').append(
                        $('<th>').text(''),
                        $('<th>').text('Module'),
                        $('<th>').text('Demo Name'),
                        $('<th>').text('IP'),
                        $('<th>').text('PORT')
                    )
                );
                for(var i = 0; i < data.length; i++){
                    console.log(data[i]);
                    var id = "func_"+data[i]['func_key'];
                    demo_list.append(
                        $('<tr>').append(
                            $('<td>').html('<br><a href="#client_session" data-func-key="'+data[i]['func_key']+'" data-client-uuid="'+data[i]['client_uuid']+'" id="'+id+'" type="button" class="btn page-scroll btn-primary page-scroll" onclick="showFunction(\''+id+'\')"> Show </a><br>'),
                            $('<td>').text(data[i]['func_scope']),
                            $('<td>').text(data[i]['func_name']),
                            $('<td>').text(data[i]['IP']),
                            $('<td>').text(data[i]['PORT'])
                        )
                    );
                }
                $('#demo_list_div').append(demo_list);
            }
        }
    );
}

// func_key has css elements in the id such as '.', so we must escape it to 
// look up using jQuery, else '.' breaks it, even thought it is valid HTML.
function jq( an_id ) {
    return "#"+an_id.replace(/(:|\.|\[|\]|,|=)/g, "\\$1");
}

function show_newline(text_string) {
    if(text_string == null){
        return "";
    }
    return text_string.replace(/\n/g, "<br/>");
}

function showFunction(element_id){
    var client_uuid = $(jq(element_id)).attr("data-client-uuid");
    var func_key = $(jq(element_id)).attr("data-func-key");
    console.log("client_uuid",client_uuid);
    console.log("func_key",func_key);
    console.log("Reqesting function info from client id:", client_uuid);
    console.log("Function id: ", func_key);

    $('#demo_title_divider').html('<hr>');
    $('#demo_client_inputs').html('');
    $('#demo_client_message').html('');
    $('#demo_client_session_div').html('');

    $.ajax({
        type: "POST",
        url: $SCRIPT_ROOT + "/request_demo",
        contentType: "application/json",
        data: JSON.stringify({'client_uuid':client_uuid,'func_key':func_key}),
        success:function(data){
            console.log("SHOWING FUNCTION!!!")
            console.log("RECIEVED",data);
            var client_session = $('<table id="client_session" align="center" width="85%" class="spacedTable>');
            $('#demo_title').html('Demo: '+data['func_name']);
            $("#demo_subtitle_divider").html("<b>Module:</b> "+data['func_scope']+"<br><p> </p><br> <b>Signature:</b> "+data['signature']);
            $("#demo_documentation").html(show_newline(data['documentation']));
            
            $('#demo_client_session_div').html('<br><p>'+JSON.stringify(data)+'</p>');
            
            var input_form = $('<table id="list_params" align="center" width="85%" class="spacedTable">');
            for(var i = 0; i < data['parameters'].length; i++){
                var input_field = $('<input>')
                input_field.attr('id',data['parameters']['name'])
                var input_field_label = $('<p>');
                input_field_label.attr('id','label_'+data['parameters'][i]['name']);
                if(data['parameters'][i]['type'] == 'standard' && data['parameters'][i]['annotation'] !== null){
                    var anno = data['parameters'][i]['annotation']
                    clean_anno = anno.replace(/</g,"");
                    clean_anno = clean_anno.replace(/>/g,"");
                    input_field_label.html('<b>'+data['parameters'][i]['name']+'<b> ('+clean_anno+')');
                } else if(data['parameters'][i]['type'] == 'standard' && data['parameters'][i]['annotation'] == null){
                    input_field_label.html('<b>'+data['parameters'][i]['name']+'<b>');
                }
                if(data['parameters'][i]['type'] == 'keyword'){
                    input_field_label.html('<b>Keyword Argument List</b> <br> comma separated values <br> i.e.: arg1=10, arg2=42.42');
                }
                if(data['parameters'][i]['type'] == 'positional'){
                    input_field_label.html('<b>Positional Argument List</b> <br> comma separated values <br> i.e.: "daimler",10,88.3');
                }
                
                if(data['parameters'][i]['default_value'] !== null){
                    input_field.attr('value',data['parameters'][i]['default_value'])
                }

                input_form.append(
                    $('<tr>').append(
                        $('<td>').html(input_field_label),
                        $('<td>').html(input_field)
                    )
                )
            }
            $('#demo_client_inputs').append(input_form);
        },
        error:function(data){
            $('#demo_client_message').html('<h1> CONNECTION FAILED </h1>');
        }
    });
}
