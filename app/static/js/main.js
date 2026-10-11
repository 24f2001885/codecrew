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

    // 8. Magnific Popup for static project links
    if ($.fn.magnificPopup) {
      $(".js-project-popup").magnificPopup({
        type: "inline",
        gallery: { enabled: true },
        mainClass: "mfp-fade"
      });
    }

    // 9. Delegated handler for member popups (supports dynamically injected cards)
    $(document).on("click", ".js-member-popup", function (e) {
      e.preventDefault();
      var target = $(this).attr("href") || $(this).data("mfp-src");
      if (target && $(target).length && $.fn.magnificPopup) {
        $.magnificPopup.open({
          items: {
            src: target,
            type: "inline"
          },
          mainClass: "mfp-fade"
        });
      }
    });

    // 10. Delegated handler for blog popups
    $(document).on("click", ".js-blog-popup", function (e) {
      e.preventDefault();
      var target = $(this).attr("href") || $(this).data("mfp-src");
      if (target && $(target).length && $.fn.magnificPopup) {
        $.magnificPopup.open({
          items: {
            src: target,
            type: "inline"
          },
          mainClass: "mfp-fade"
        });
      }
    });

    // 11. Smooth Scrolling for in-page anchors
    $('a[href^="#"]:not(.js-member-popup):not(.js-project-popup):not(.js-blog-popup):not([data-toggle])').on("click", function (e) {
      var href = $(this).attr("href");
      if (!href || href === "#") return;
      var target = $(href);
      if (target.length) {
        e.preventDefault();
        var navHeight = $("#ftco-navbar").outerHeight() || 70;
        $("html, body").stop().animate({
          scrollTop: target.offset().top - navHeight
        }, 600);
      }
    });

    // 12. Hero Canvas Particle Starfield
    initHeroParticles();

    // 13. Command Palette (Cmd+K / Ctrl+K)
    initCommandPalette();
  });

  // Hero Canvas Particles
  function initHeroParticles() {
    var canvas = document.getElementById("hero-particles");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) return;

    var width, height;
    var particles = [];
    var numParticles = window.innerWidth < 768 ? 18 : 36;
    var mouse = { x: -1000, y: -1000 };

    function resize() {
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    window.addEventListener("mousemove", function (e) {
      var rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });

    for (var i = 0; i < numParticles; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 1.8 + 1,
        color: Math.random() > 0.4 ? "rgba(241, 178, 75, " : "rgba(56, 189, 248, ",
        alpha: Math.random() * 0.5 + 0.2
      });
    }

    function loop() {
      ctx.clearRect(0, 0, width, height);

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        var dxMouse = mouse.x - p.x;
        var dyMouse = mouse.y - p.y;
        var distMouse = Math.sqrt(dxMouse * dxMouse + dyMouse * dyMouse);
        if (distMouse < 120) {
          p.x -= (dxMouse / distMouse) * 0.6;
          p.y -= (dyMouse / distMouse) * 0.6;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color + p.alpha + ")";
        ctx.fill();

        for (var j = i + 1; j < particles.length; j++) {
          var p2 = particles[j];
          var dx = p.x - p2.x;
          var dy = p.y - p2.y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            var lineAlpha = (1 - dist / 110) * 0.16;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = "rgba(241, 178, 75, " + lineAlpha + ")";
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  // Global Toast Notifications
  window.showToast = function (message, type) {
    var $container = $("#cc-toast-container");
    if (!$container.length) {
      $container = $('<div id="cc-toast-container" class="position-fixed" style="bottom: 24px; right: 24px; z-index: 999999; display: flex; flex-direction: column; gap: 10px;"></div>');
      $("body").append($container);
    }
    var badgeColor = type === "success" ? "#a0f669" : "#f1b24b";
    var $toast = $(
      '<div class="cc-toast shadow-lg py-3 px-4 d-flex align-items-center" style="background: rgba(17, 24, 39, 0.95); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.12); border-left: 4px solid ' + badgeColor + '; border-radius: 10px; color: #f8fafc; font-size: 0.9rem; font-weight: 500; min-width: 260px; transform: translateY(20px); opacity: 0; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);">' +
        '<span class="mr-2" style="color: ' + badgeColor + ';">✔</span>' +
        '<span>' + message + '</span>' +
      '</div>'
    );
    $container.append($toast);
    setTimeout(function () {
      $toast.css({ transform: "translateY(0)", opacity: 1 });
    }, 10);
    setTimeout(function () {
      $toast.css({ transform: "translateY(-10px)", opacity: 0 });
      setTimeout(function () { $toast.remove(); }, 300);
    }, 3200);
  };

  // 1-Click Clipboard Share Handler
  $(document).on("click", ".js-copy-link", function (e) {
    e.preventDefault();
    var url = $(this).data("url") || window.location.href;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () {
        window.showToast("Link copied to clipboard!", "success");
      }).catch(function () {
        window.showToast("Link copied to clipboard!", "success");
      });
    } else {
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val(url).select();
      document.execCommand("copy");
      $temp.remove();
      window.showToast("Link copied to clipboard!", "success");
    }
  });

  // Command Palette Handler
  function initCommandPalette() {
    $(document).on("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        $("#ccCommandPalette").modal("toggle");
      }
    });

    $("#ccCommandPalette").on("shown.bs.modal", function () {
      $("#ccPaletteInput").focus().val("");
      $(".cc-palette-item").show();
      $("#ccPaletteEmpty").hide();
    });

    $("#ccPaletteInput").on("input", function () {
      var term = $(this).val().toLowerCase().trim();
      var visibleCount = 0;
      $(".cc-palette-item").each(function () {
        var text = $(this).text().toLowerCase();
        if (!term || text.indexOf(term) !== -1) {
          $(this).show();
          visibleCount++;
        } else {
          $(this).hide();
        }
      });
      if (visibleCount === 0) {
        $("#ccPaletteEmpty").show();
      } else {
        $("#ccPaletteEmpty").hide();
      }
    });
  }

  // Expose effect re-initializer for dynamically injected DOM (guarded against double execution)
  window.initPublicEffects = function (rootEl) {
    var $root = rootEl ? $(rootEl) : $(document);
    if ($root.data("effects-initialized")) {
      return;
    }
    $root.data("effects-initialized", true);

    if (typeof AOS !== "undefined") {
      AOS.refresh();
    }
  };

})(jQuery);
