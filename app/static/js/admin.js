(function ($) {
  "use strict";

  $(document).ready(function () {
    // Delete confirm modal or confirmation alerts
    $(".btn-confirm-delete").on("click", function (e) {
      if (!confirm("Are you sure you want to delete this record? This action cannot be undone.")) {
        e.preventDefault();
      }
    });
  });
})(jQuery);
