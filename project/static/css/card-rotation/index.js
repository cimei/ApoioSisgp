$('.flippe').on('click', function () {
      var target = $(this).closest('.flipper');
      target.toggleClass('flipped');
  });