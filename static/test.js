$(document).ready( function() {
	test();
});


function test() {
	$('#post').click(function() {

		$.ajax({
			type: "POST",
			url: "http://localhost:5000/addEmailListing",
			data: '{ "emailAddress" : "test@test" }',
			dataType: "json",
			contentType: "application/json",
			success: function(data, textStatus, xhr) {
				console.log(xhr);
				console.log(".success");
			},
			error: function(xhr, textStatus) {
				//
				console.log(xhr);
				console.log('.error');
			},
			complete: function(xhr, textStatus) {
				console.log(xhr);
				console.log('.complete');
			}
		});
	});

}