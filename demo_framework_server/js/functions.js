function getDemos(){
    $.ajax({
        type : "GET",
        url : $SCRIPT_ROOT + "/request_demo_list",
        contentType : "application/json",
        success : function(data) {
            console.log("Requested Demo List: ", data);
                var demo_list = $('<table id="demo_list" align="center" width="85%" class="spacedTable">')
                $('#demo_list_div').html('')
                demo_list.append(
                    $('<tr>').append(
                        $('<th>').text(''),
                        $('<th>').text('Demo Name'),
                        $('<th>').text('IP'),
                        $('<th>').text('PORT')
                    )
                );
                for(var i = 0; i < data.length; i++){
                    console.log(data[i]);
                    var id = "func_"+data[i]['func_uuid'];
                    demo_list.append(
                        $('<tr>').append(
                            $('<td>').html('<br><a href="#demo_client_session" data-func-uuid="'+data[i]['func_uuid']+'" data-client-uuid="'+data[i]['client_uuid']+'" id="'+id+'" type="button" class="btn page-scroll btn-primary" onclick="showFunction(\''+id+'\')"> Show </a><br>'),
                            $('<td>').text(data[i]['name']),
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

function showFunction(element_id){
    var elem = document.getElementById(element_id);
    var client_uuid = $("#"+element_id).attr("data-func-uuid");
    var func_uuid = $("#"+element_id).attr("data-client-uuid");
    console.log("Reqesting function info from client id:", client_uuid);
    console.log("Function id: ", func_uuid);

    $.ajax({
        type: "POST",
        url: $SCRIPT_ROOT + "/request_demo",
        contentType: "application/json",
        success:function(data){
            console.log("SHOWING FUNCTION!!!");
        }
    });
}
