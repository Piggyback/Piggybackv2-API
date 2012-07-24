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

		if(email.length == 0) {
			// nice try. we only take email addresses that aren't empty.
			comment = "Nice try! It appears that your email is invisible.";
		} else if(validateEmail(email)) {
			// email is valid
			submitEmail();
			$('.carousel').carousel('next');
			$('.carousel').carousel('pause');
		} else {
			// email is invalid
			var r = Math.floor(Math.random() * 3) + 1;
			switch(r) {
				case 1:
					comment = "Almost! Try adding a \"@\" somewhere in there.";
					break;
				case 2:
					comment = "Sorry, but it's got to be an email address.";
					break;
				case 3:
					comment = "Oops, doesn't seem that is a proper email."
					break;
			}
		}

		// update the comment div
		$('#form-invalidate-comment').html("<p>" + comment + "</p>");	// reset the comment div
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
		url: "http://piggybackv2.herokuapp.com/addEmailListing",
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
}