$(document).ready( function() {
	$('.carousel').carousel('pause');
	initShowNotes();
	initValidateEmailForm();
	initModifyEnterSubmit();
});

function initShowNotes() {
	$('.show-notes').hover(
		function () {
			var id = $(this).attr('id');
			var targetId = "#piggyback-" + id + "-notes";
			$(targetId).removeClass("none");
		},
		function () {
			var id = $(this).attr('id');
			var targetId = "#piggyback-" + id + "-notes";
			$(targetId).addClass("none");
		}
	)
}

function initValidateEmailForm() {
	$('#submit-email-button').click(function() {
		var email = $.trim($('#email-input').val());
		var comment = "";

		$('.carousel').carousel('next');
		$('.carousel').carousel('pause');
		// testing
		submitEmail();

		// if(email.length == 0) {
		// 	// nice try. we only take email addresses that aren't empty.
		// 	comment = "<p>Nice try! But we are looking for an email address.</p>";
		// } else if(validateEmail(email)) {
		// 	// email is valid
		// 	submitEmail();
		// 	$('.carousel').carousel('next');
		// 	$('.carousel').carousel('pause');
		// } else {
		// 	// email is invalid
		// 	comment = "<p>Almost! Try adding a \"@\" somewhere in there.</p>";
		// }

		// // update the comment div
		// $('#form-invalidate-comment').html(comment);	// reset the comment div
	})
}

function validateEmail(email) {
	var filter = /^([\w-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([\w-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/;
	if(filter.test(email)) {
		return true;
	} else {
		return false;
	}
}

function initModifyEnterSubmit() {
	$('#email-input').keypress(function(e) {
		if(e.which == 13) {
			$('#submit-email-button').click();
			e.preventDefault;
			return false;
		}
	})
}

function submitEmail() {
	var email = $('#email-input').val();

	$.ajax({
		type: "POST",
		url: "http://localhost:5000/addEmailListing",
		data: '{ "emailAddress" : "' + email + '" }',
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

	// crossDomainPost(email);

}

// function crossDomainPost(email) {
// 	// Add the iframe with a unique name
// 	var iframe = document.createElement("iframe");
// 	var uniqueString = "piggybackEmailPost";
// 	document.body.appendChild(iframe);
// 	iframe.style.display = "none";
// 	iframe.contentWindow.name = uniqueString;
// 	$('iframe').attr('id', uniqueString);

// 	// construct a form with hidden inputs, targeting the iframe
// 	var form = document.createElement("form");
// 	form.target = uniqueString;
// 	form.action = "http://piggybackv2.herokuapp.com/addEmailListing";
// 	form.method = "POST";


// 	// repeat for each parameter
// 	var input = document.createElement("input");
// 	input.type = "hidden";
// 	input.name = "emailAddress";
// 	input.value = email;
// 	form.appendChild(input);

// 	document.body.appendChild(form);
// 	form.submit();
// }
