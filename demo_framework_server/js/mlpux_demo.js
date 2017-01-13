function initializeUI(){
    clearDemos();
    getDemos();
}

function clearDemoOutput(){
    $("#demo_results").html('');
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
    $("#demo_confirm_exe").html('');
    $("#demo_results").html('');
    $("#execute_demo").html('');
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
    $("#demo_confirm_exe").html('');
    $("#demo_results").html('');
    $("#execute_demo").html('');

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
           
            if(data['documentation'] !== null){
                var docstring = data['documentation'].replace(/\s\s+/g, ' ');
                var docstring = docstring.replace(/\n/g,' ');
                data['documentation'] = docstring;
            }
            var display_attribs = $('<pre>').append(
                $('<code>').append(JSON.stringify(data,null,4)
                )
            );
            $("#demo_client_session_div").append(display_attribs);
            
            var input_form = $('<table id="list_params" align="center" width="85%" class="spacedTable">');
            if(data['parameters'].length == 0){
                var input_field = $('<div class="inputParameter" data-func-scope="'+data['func_scope']+'" data-arg-type="noargs" data-func-name="'+data['func_name']+'">');
                input_form.append(input_field)
            }
            for(var i = 0; i < data['parameters'].length; i++){
                var input_field = $('<input id="'+data['parameters'][i]['name']+'" class="inputParameter" data-func-scope="'+data['func_scope']+'" data-arg-type="'+data['parameters'][i]['type']+'" data-func-name="'+data['func_name']+'">');
                var input_field_label = $('<p>');
                if(data['parameters'][i]['type'] == 'standard' && data['parameters'][i]['annotation'] !== null){
                    var anno = data['parameters'][i]['annotation']
                    clean_anno = anno.replace(/</g,"");
                    clean_anno = clean_anno.replace(/>/g,"");
                    input_field_label.html('<b>'+data['parameters'][i]['name']+'</b> ('+clean_anno+')');
                } else if(data['parameters'][i]['type'] == 'standard' && data['parameters'][i]['annotation'] == null){
                    input_field_label.html('<b>'+data['parameters'][i]['name']+'<b>');
                }
                if(data['parameters'][i]['type'] == 'keyword'){
                    input_field_label.html('<b>Keyword Argument List</b> <br> comma separated values <br> i.e.: arg1=10, arg2=42.42');
                }
                if(data['parameters'][i]['type'] == 'positional'){
                    input_field_label.html('<b>Positional Argument List</b> <br> comma separated values <br> i.e.: "daimler", 10, 88.3');
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
            var execute_button = $("<input>");
            execute_button.attr('id','execute_demo_button');
            execute_button.attr('onclick',"sendFunctionArguments()");
            execute_button.attr('type','button');
            execute_button.attr('class','btn btn-xl btn-primary');
            execute_button.attr('value','Execute Demo');
            var clear_output = $("<input>");
            clear_output.attr('id','clear_output_button');
            clear_output.attr('onclick',"clearDemoOutput()");
            clear_output.attr('type','button');
            clear_output.attr('class','btn btn-xl btn-primary');
            clear_output.attr('value','Clear Output');
            $("#execute_demo").append(execute_button);
            $("#execute_demo").append(clear_output);
        },
        error:function(data){
            $('#demo_client_message').html('<h1> CONNECTION FAILED </h1>');
        }
    });
}

function sendFunctionArguments(){
    console.log("SENDING ARGS");
    var func_scope = null
    var func_name = null
    var payload = {}

    $( ".inputParameter" ).each(function( index ) {
        func_scope = $(this).attr('data-func-scope');
        func_name = $(this).attr('data-func-name');
        var type = $(this).attr('data-arg-type');
        if(type == 'positional'){
            payload.args = JSON.stringify($(this).val().split(","));
        } else if(type == 'keyword'){
            var temp = $(this).val().split(",");
            for(var i = 0; i < temp.length; i++){
                var temp2 = temp[i].split('=');
                payload[temp2[0]] = temp2[1];
            }
        } else if (type =="noargs") {
            payload.args = []
        } 
        else {
            payload[$(this).attr('id')] = $(this).val();
        }
    });

    console.log( "Data ready:", func_scope, func_name, payload);
    var endpoint = '/execute/'+func_scope+'/'+func_name

    // Now post the data to the engineering server.
    $.ajax({
        url:$SCRIPT_ROOT+endpoint,
        type:"GET",
        data:payload,
        success:function(data){
            console.log("RESPONSE",data);
            if(data['msg'] == 'success'){
                // <div id="demo_confirm_exe"> </div>
                // <div id="demo_results"> </div>
                var result = $('<h2>').text(JSON.stringify(data['result'],null,4));
                $("#demo_results").append(result);
            }
            if( 'error' in data ){
                var result = $('<h2>').text(JSON.stringify(data['error'],null,4));
                $("#demo_results").append(result);
            }
        },
        error:function(data){
            console.log("ERROR WITH EXECUTION");
                $("#demo_results").append(result);
        }
    });
}
