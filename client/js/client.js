window.onload=function(){
	var socket = new WebSocket('ws://localhost:3369');

	socket.onopen = function(){
		console.log('socket open');
		$('#send').click(function(){
			var data = $('#client_text').val();
			if(data){
				socket.send(data);
				$('#client_text').val('');
				console.log('click');
			}
		});
	}

	socket.onmessage = function(result){
		$('#server_text').val(result.data);
		console.log(result.data);
	}

	socket.onclose = function(evt){
		console.log('socket close');
	}

	socket.onerror = function(evt) { 
        console.log('error:')
    };
}

