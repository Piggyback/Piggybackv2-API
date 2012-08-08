$(document).ready( function() {
	
	// splash-home
	$('.carousel').carousel('pause');
	initShowNotes();
	initValidateEmailForm();
	initModifyEnterSubmit();

	// about
	initScrollNextButton();
	initShowCharacterNotes();

	// hover team page
	initShowProfilePics();

	// init demo scroll button
	initDemoScrollButton();
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

			// hide div and replace it with "Great! Stay tuned for updates!"
			$('#sign-up').html('<h3>Somewhere in the world a little bell just rang—we got your email!</h3>');
			$('#sign-up').css('color', 'grey');

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


function initShowCharacterNotes() {
	$('.on-hover').hover(
		function () {
			// make every other image opacity .1
			$('.character-img').css('opacity', '0.05');
			// $('.character-img').css('z-index', '0');

			// make hover target opacity = 1
			var id = "#" + $(this).attr('id');
			$(id).css('opacity', '1');
			// $(id).css('z-index', '2');

			// show notes specific to target
			id = id + "-notes";
			$(id).removeClass("none");
			$(id).css('z-index', '-1');
		},
		function () {
			// make all opacity the same
			$('.character-img').css('opacity', '1');

			// get target id
			var id = "#" + $(this).attr('id') + "-notes";

			// remove notes specific to target
			$(id).addClass("none");
		}
	)
}

function initShowProfilePics() {
	$('.headshot').hover(
		function () {
			// show real pic
			$(this).closest('section').find('.real').removeClass('none');
		},
		function () {
			$(this).closest('section').find('.real').addClass('none');
		}
	)
}

function initScrollNextButton() {
	$('#next-button').click(function() {
		goToByScroll("ob-2");
	})

	$('#sign-up-now-button').click(function() {
		goToByScroll("ob-5");
	})

	$(window).scroll(function() {
		var y = $(window).scrollTop();
		var target = "2";

		$('#next-button').removeClass('none');
		$('#sign-up-now-button').removeClass('none');

		switch (true) {
			case y < 840:
				target = "2";
				break;
			case y < 1640:
				target = "3";
				break;
			case y < 2440:
				target = "4";
				break;
			case y < 3240:
				target = "5";
				break;
			case y + $(window).height() + 100 > $(document).height():
				// change the button to redirect to the signup page?
				$('#next-button').addClass('none');
				$('#sign-up-now-button').addClass('none');
				break;
			default:
				target = "1";
				break;
		}
		console.log(y);

		$('#next-button').unbind()
						   .click(function() {
			goToByScroll("ob-" + target);
		})
	})
}

function initDemoScrollButton() {
	$('#demo-scroll-button').click( function() {
		$('html, body').animate({
			scrollTop: $(document).height() - $(window).height()},
			15000, "linear", function() {}
		);
		return false;
	})
}

function goToByScroll(id) {
	$('html,body').animate({scrollTop: $('#'+id).offset().top + 50}, 'slow');
}