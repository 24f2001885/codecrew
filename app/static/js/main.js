(function ($) {
  "use strict";

  // Hide loader when document is ready
  $(document).ready(function () {
    var loader = function () {
      setTimeout(function () {
        if ($("#ftco-loader").length > 0) {
          $("#ftco-loader").removeClass("show");
        }
      }, 100);
    };
    loader();

    // Init AOS animation library if present
    if (typeof AOS !== "undefined") {
      AOS.init({
        duration: 800,
        easing: "slide",
        once: true
      });
    }
  });
})(jQuery);
