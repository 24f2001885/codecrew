(function ($) {
  "use strict";

  $(document).ready(function () {
    // 1. Confirm Delete Modal Handler
    $(document).on("click", "[data-confirm-body]", function (e) {
      e.preventDefault();
      var $btn = $(this);
      var title = $btn.attr("data-confirm-title") || "Confirm Deletion";
      var body = $btn.attr("data-confirm-body") || "Are you sure you want to delete this item?";
      var action = $btn.attr("data-confirm-action") || "";

      $("#confirm-modal-title").text(title);
      $("#confirm-modal-body").text(body);
      $("#confirm-modal-form").attr("action", action);

      // Show Bootstrap modal
      if (typeof $("#confirm-modal").modal === "function") {
        $("#confirm-modal").modal("show");
      }
    });

    // 2. Auto-dismiss alerts after 5 seconds
    setTimeout(function () {
      $(".flash-container .alert").fadeOut(500, function () {
        $(this).remove();
      });
    }, 5000);
  });
})(jQuery);
