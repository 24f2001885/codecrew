(function ($) {
  "use strict";

  $(document).ready(function () {
    // 1. Loader fade out
    if ($("#ftco-loader").length > 0) {
      setTimeout(function () {
        $("#ftco-loader").removeClass("show");
      }, 100);
    }

    // 2. Navbar scroll effect
    $(window).scroll(function () {
      var st = $(this).scrollTop();
      if (st > 150) {
        $("#ftco-navbar").addClass("scrolled");
      } else {
        $("#ftco-navbar").removeClass("scrolled");
      }
    });

    // 3. Flash messages auto-dismiss after 5s
    setTimeout(function () {
      $(".flash-container .alert").fadeOut(500, function () {
        $(this).remove();
      });
    }, 5000);

    // 4. AOS Initialization
    if (typeof AOS !== "undefined") {
      AOS.init({
        duration: 800,
        easing: "slide",
        once: true
      });
    }

    // 5. Owl Carousels
    if ($.fn.owlCarousel) {
      $(".hero-carousel").owlCarousel({
        items: 1,
        loop: true,
        autoplay: true,
        autoplayTimeout: 5000,
        animateOut: "fadeOut",
        nav: false,
        dots: true
      });

      $(".featured-carousel").owlCarousel({
        loop: true,
        margin: 20,
        nav: false,
        dots: true,
        responsive: {
          0: { items: 1 },
          768: { items: 2 },
          992: { items: 3 }
        }
      });
    }

    // 6. Stellar Parallax
    if ($.fn.stellar) {
      $(window).stellar({
        horizontalScrolling: false,
        verticalOffset: 40
      });
    }

    // 7. Stat Counters
    if (typeof Waypoint !== "undefined" && $.fn.animateNumber) {
      $(".number").each(function () {
        var $el = $(this);
        var targetNum = parseInt($el.attr("data-number"), 10) || 0;
        new Waypoint({
          element: this,
          handler: function () {
            $el.animateNumber({ number: targetNum }, 1200);
            this.destroy();
          },
          offset: "95%"
        });
      });
    }

    // 8. Magnific Popup
    if ($.fn.magnificPopup) {
      $(".js-project-popup").magnificPopup({
        type: "inline",
        gallery: { enabled: true },
        mainClass: "mfp-fade"
      });
    }

    // 9. Smooth Scrolling for in-page anchors
    $('a[href^="#"]').on("click", function (e) {
      var target = $(this.getAttribute("href"));
      if (target.length) {
        e.preventDefault();
        var navHeight = $("#ftco-navbar").outerHeight() || 70;
        $("html, body").stop().animate({
          scrollTop: target.offset().top - navHeight
        }, 600);
      }
    });
  });

  // Expose effect re-initializer for dynamically injected DOM (used in P5)
  window.initPublicEffects = function (rootEl) {
    if (typeof AOS !== "undefined") {
      AOS.refresh();
    }
  };

})(jQuery);
