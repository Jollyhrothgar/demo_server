function initializeUI(){
    clearDemos();
    getDemos();
}

function clearDemoOutput(){
    $("#demo_results").html('');
    map.panTo(sunnyvale);
    map.setCenter(sunnyvale);
    for(var i = 0; i < map_points.length; i++){
        map_points[i].setMap(null)
    }
}


/// MAP STUFF 

// Global Map Variable
var map;// handle for talking to map
var map_points = []; // any time map is updated store google.maps pointers here.
var sunnyvale = {lat: 37.386044, lng: -122.036287};
 
function initMap(){
    console.log("google called back");
    map = new google.maps.Map(document.getElementById('location_map'), {
        center:sunnyvale, // Sunnyvale
        zoom: 13,
        scrollwheel:false,
    });
}

function recenterMap(lattitude, longitude){
    map.setCenter({lat:parseFloat(lattitude),lng:parseFloat(longitude)});
}

// Takes a list of {lat:coordinate, lng:coordinate} objects and plots them
function plotPoints(center, coordinates){
    // clear all the markers
    
    map.panTo(center);
    map.setCenter(center);
    for(var i = 0; i < map_points.length; i++){
        map_points[i].setMap(null)
    }
    map_points.length = 0;
    for(var i = 0; i < coordinates.length; i++){
        var marker = new google.maps.Marker({
            position: new google.maps.LatLng(coordinates[i]),
            map:map
        });
        map_points.push(marker);
    }
}
/// END MAP STUFF

function clearDemos(){
    $('#demo_list_div').html('');
    $('#demo_executables').html('');
    $('#demo_selector_div').html('');
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
    $("#location_map").hide();
}

function showDemo(func_scope){
    $('.hidable').each(function (index) {
        //console.log(index, this);
        $(this).hide();
        if($(this).attr('data-func-scope') == func_scope )  {
            $(this).show();
        }
    });
    console.log($(".hidable"));
}

function getDemos(){
    clearDemos();
    $.ajax({
        type : "GET",
        url : $SCRIPT_ROOT + "/request_demo_list",
        contentType : "application/json",
        success : function(data) {
            console.log("Requested Demo List: ", data);
            if (data.length == 0){
                return
            } 
            var demo_executable = $('<table>');
            demo_executable.attr('id',"demo_executable")
            demo_executable.attr('align',"center");
            demo_executable.attr('width',"85%");
            demo_executable.addClass("spacedTable");
            demo_executable.attr('data-func-scope',data[0]['func_scope']);
            $('#demo_executables').html('') // this resets anything already in the div
            var header_table = {};
            for(var i = 0; i < data.length; i++){
                console.log(data[i]);
                var id = "func_"+data[i]['func_key'];
                var button = $('<br><a>');
                header_table[data[i]['func_scope']] = { 'func_scope':data[i]['func_scope'], 'IP':data[i]['IP'], 'PORT':data[i]['PORT'] };
                button.attr('href','#client_session');
                button.attr('data-func-key',data[i]['func_key']);
                button.attr('data-client-uuid',data[i]['client_uuid']);
                button.attr('id',id);
                button.attr('type','button');
                button.addClass('btn');
                button.addClass('page-scroll');
                button.addClass('btn-primary');
                button.attr('onclick','showFunction(\''+id+'\')');
                button.append('Select');

                var row = $('<tr>').append(
                    $('<td>').append(button),
                    $('<td>').text(data[i]['func_scope']),
                    $('<td>').text(data[i]['func_name']),
                    $('<td>').text(data[i]['IP']),
                    $('<td>').text(data[i]['PORT'])
                );
                row.addClass('hidable');
                row.attr('data-func-scope',data[i]['func_scope']);
                demo_executable.append(row);
            }
            $('#demo_executables').append(demo_executable);

            var demo_selector = $('<table>');
            demo_selector.attr('id','demo_selector');
            demo_selector.attr('align','center');
            demo_selector.attr('width','85%');
            demo_selector.addClass('spacedTable');
            demo_selector.append(
                $('<tr>').append(
                    $('<th>').text(''),
                    $('<th>').text('Module'),
                    $('<th>').text('IP'),
                    $('<th>').text('PORT')
                )
            );

            for(var func_scope in header_table){
                var demo_button = $('<br><a>');
                demo_button.attr('id','demo_show_button');
                demo_button.attr('type','button');
                demo_button.addClass('btn');
                demo_button.addClass('btn-primary');
                demo_button.attr('onclick','showDemo(\''+func_scope+'\')');
                demo_button.append('Show');
                demo_selector.append(
                    $('<tr>').append(
                        $('<td>').append(demo_button),
                        $('<td>').append(func_scope),
                        $('<td>').append(header_table[func_scope]['IP']),
                        $('<td>').append(header_table[func_scope]['PORT'])
                    )
                );
            }
            $("#demo_selector_div").append(demo_selector);
            $('.hidable').each(function (index) {
                //console.log(index, this);
                $(this).hide();
            });
        }
    });
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

function make_param_label(name, type, annotation){
    var label = $('<p>');
    if(type == 'standard' && annotation !== null){
        var anno = annotation
        clean_anno = anno.replace(/</g,"");
        clean_anno = clean_anno.replace(/>/g,"");
        label.append(('<b>'+name+'</b> ('+clean_anno+')'));
    } else if(type == 'standard' && annotation == null){
        label.append('<b>'+name+'<b>');
    }
    if(type == 'keyword'){
        label.append('<b>Keyword Argument List</b> <br> comma separated values <br> i.e.: arg1=10, arg2=42.42');
    }
    if(type == 'positional'){
        label.append('<b>Positional Argument List</b> <br> comma separated values <br> i.e.: "daimler", 10, 88.3');
    }
    return label;
}

function echo_param_output(param_id, echo_id){
    var value = $("#"+param_id).val();
    $("#"+echo_id).text(value);
}

function make_input_slider(param, data_func_scope, data_func_name){
    var input_field = $('<input>');
    var echo_id = 'echo_'+param.name;
    input_field.attr('id',param.name);
    input_field.attr('type','range');
    input_field.attr('min', param.param_gui.min);
    input_field.attr('max', param.param_gui.max);
    input_field.attr('step', param.param_gui.ndiv);
    input_field.attr('class','inputParameter');
    input_field.attr('data-func-scope',data_func_scope);
    input_field.attr('data-arg-type',param['type']);
    input_field.attr('data-func-name',data_func_name);
    input_field.attr('onchange','echo_param_output("'+param.name+'","'+echo_id+'")');
    
    if(param.default_value !== null){
        input_field.attr('value',param.default_value);
    }
    var input_field_label = make_param_label(param.name, param.type, param.annotation);
    var widget = {label:input_field_label, field:input_field};
    return widget
}

function make_input_field(param, data_func_scope, data_func_name){
    var input_field = $('<input>');
    input_field.attr('id',param.name);
    input_field.attr('class','inputParameter');
    input_field.attr('data-func-scope',data_func_scope);
    input_field.attr('data-arg-type',param['type']);
    input_field.attr('data-func-name',data_func_name);
    
    if(param.default_value !== null){
        input_field.attr('value',param.default_value);
    }
    var input_field_label = make_param_label(param.name, param.type, param.annotation);
    var widget = {label:input_field_label, field:input_field};
    return widget
}

function make_input_widget(param, data_func_scope, data_func_name ){
    var widget = ""
    console.log(param.param_gui);
    if (param.param_gui == null){
        widget = make_input_field(param, data_func_scope, data_func_name);
    } else if (param.param_gui.hasOwnProperty("slider")) {
        console.log("SLLLLIIIIDERRRRR",param.param_gui)
        widget = make_input_slider(param, data_func_scope, data_func_name);
    }
    return widget
}

function showFunction(element_id){
    var client_uuid = $(jq(element_id)).attr("data-client-uuid");
    var func_key = $(jq(element_id)).attr("data-func-key");
    console.log("client_uuid",client_uuid);
    console.log("func_key",func_key);
    console.log("Reqesting function info from client id:", client_uuid);
    console.log("Function id: ", func_key);

    // Calling showDemo with null ensures nothing is matched and therefore the
    // table is hidden.
    showDemo(null);

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
                var widget = make_input_widget(
                    data['parameters'][i],
                    data['func_scope'],
                    data['func_name']
                );

                input_form.append(
                    $('<tr>').append(
                        $('<td>').html(widget.label),
                        $('<td>').html(widget.field),
                        $('<td>').html('<p id="echo_'+data['parameters'][i]['name']+'"></p>')
                    )
                );
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
            var plot_something = $("<input>");
            plot_something.attr('id','plot_testing');
            plot_something.attr('onclick','makeTestPlot()');
            plot_something.attr('type','button');
            plot_something.attr('class','btn btn-xl btn-primary');
            plot_something.attr('value','Test Plot Interface');
            $("#execute_demo").append(execute_button);
            $("#execute_demo").append(clear_output);
            $("#execute_demo").append(plot_something);
        },
        error:function(data){
            getDemos();
            $('#demo_client_message').html('<h1> CONNECTION FAILED </h1>');
        }
    });
}
 

/*
$("#query").click(function() {  

  $("#loading-div-background").show();
  $("#container").hide();
  var plot_type = $('input:radio[name=plot_type]:checked').val();
  var qu = {"plot_type":plot_type}
  $.ajax({
    type: "POST",
    async:true,
    contentType: "application/json; charset=utf-8",
    url: "/query",
    data: JSON.stringify(qu),
    success: function (data) {     
     var graph = $("#container");
     graph.html(data);   
     $("#loading-div-background").hide();      
     $("#container").show();
   },
   dataType: "html"
 });
});

*/
function makeTestPlot(){
    console.log('PLOTTING');
    var endpoint = '/test_plot';
    $.ajax({
        url:$SCRIPT_ROOT+endpoint,
        type:"GET",
        success:function(data){
            console.log("RESPONSE",data);
            var graph = $("#development_testing");
            graph.html(data);
            $('#development_testing').show();
            $("#development_testing").html(data);
        },
        error:function(data){
            console.log("ERROR WITH EXECUTION");
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
            if( data.hasOwnProperty('msg') ){
                if (data['msg'] == 'success') {
                    if ( data.hasOwnProperty('display') ){
                        if( data['display'] == 'map' ) {
                            $("#location_map").show();
                            console.log('making a map');
                            $("#demo_results").append("See the map!");
                            plotPoints(data['center'],data['points']);
                            $('html,body').animate({scrollTop:$('#location_map').offset().top}, 'slow');
                        } else if (data['display'] == 'plot') {
                            console.log('making a plot');
                            $("#demo_results").append(data['plot_soup']);
                            //$("#demo_results").html(data);

                        } else if (data['display'] == 'table'){
                            console.log('making a table');
                            $("#demo_results").append(data['table_soup']);

                        } else if (data['display'] == 'plain') {
                            console.log('dumping json');
                            var plain_display = $('<pre>').append(
                                $('<code>').append(JSON.stringify(data,null,4)
                                )
                            );
                            $("#demo_results").append(plain_display);
                        }
                    }
                }
            } else if( data.hasOwnProperty('error') ){
                console.log("ERROR HERE");
                getDemos();
                error_msg = $('<h2>').append("Problem with execution");
                error_msg.append(data['error']);
                $("#demo_results").append($('<h2>').append(error_msg));
            } else {
                console.log('UNHANDLED DISPLAY OUTPUT');
                var result = $('<h2>').append(JSON.stringify(data,null,4));
                result.append("THIS WAS NOT PROPERLY HANDLED AND IS UNEXPECTED");
                $("#demo_results").append(result);
            }
        },
        error:function(data){
            console.log("ERROR WITH EXECUTION");
            $("#demo_results").append("EXECUTION ERROR - AJAX REQUEST FAILED");
        }
    });
}
