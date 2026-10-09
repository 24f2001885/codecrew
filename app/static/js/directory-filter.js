(function ($) {
  "use strict";

  $(document).ready(function () {
    var $filter = $("#directory-filter");
    if (!$filter.length) {
      return;
    }

    var endpoint = $filter.data("endpoint");
    var kind = $filter.data("kind"); // 'groups' or 'members'
    if (!endpoint) {
      return;
    }

    // Read initial state from URL query params
    var urlParams = new URLSearchParams(window.location.search);
    var q = urlParams.get("q") || "";
    var tagOrSkill = kind === "groups" ? (urlParams.get("tag") || "") : (urlParams.get("skill") || "");
    var group = urlParams.get("group") || "";
    var page = parseInt(urlParams.get("page"), 10) || 1;

    var currentRequestId = 0;
    var debounceTimer = null;

    function buildUrlParams() {
      var params = new URLSearchParams();
      if (q) params.set("q", q);
      if (kind === "groups") {
        if (tagOrSkill) params.set("tag", tagOrSkill);
      } else {
        if (tagOrSkill) params.set("skill", tagOrSkill);
        if (group) params.set("group", group);
      }
      if (page > 1) params.set("page", page);
      return params;
    }

    function updateBrowserUrl() {
      var params = buildUrlParams();
      var queryString = params.toString();
      var newUrl = window.location.pathname + (queryString ? "?" + queryString : "");
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", newUrl);
      }
    }

    function renderPagination(currentPage, totalPages) {
      var $nav = $("#directory-pagination");
      if (!$nav.length) return;

      if (totalPages <= 1) {
        $nav.empty();
        return;
      }

      var html = '<ul class="pagination justify-content-center">';
      // Previous
      if (currentPage > 1) {
        html += '<li class="page-item"><a class="page-link bg-dark text-warning border-secondary js-page-link" href="#" data-page="' + (currentPage - 1) + '">&laquo; Prev</a></li>';
      } else {
        html += '<li class="page-item disabled"><span class="page-link bg-dark text-muted border-secondary">&laquo; Prev</span></li>';
      }

      // Pages
      for (var p = 1; p <= totalPages; p++) {
        if (p === currentPage) {
          html += '<li class="page-item active"><span class="page-link bg-warning text-dark border-warning font-weight-bold">' + p + '</span></li>';
        } else {
          html += '<li class="page-item"><a class="page-link bg-dark text-light border-secondary js-page-link" href="#" data-page="' + p + '">' + p + '</a></li>';
        }
      }

      // Next
      if (currentPage < totalPages) {
        html += '<li class="page-item"><a class="page-link bg-dark text-warning border-secondary js-page-link" href="#" data-page="' + (currentPage + 1) + '">Next &raquo;</a></li>';
      } else {
        html += '<li class="page-item disabled"><span class="page-link bg-dark text-muted border-secondary">Next &raquo;</span></li>';
      }

      html += '</ul>';
      $nav.html(html);
    }

    function fetchResults() {
      var requestId = ++currentRequestId;
      var params = buildUrlParams();

      $.getJSON(endpoint + "?" + params.toString())
        .done(function (data) {
          if (requestId !== currentRequestId) {
            return; // Ignore stale responses
          }

          var $results = $("#directory-results");
          var $status = $("#directory-status");

          // 1. Status line
          var total = data.total_count || 0;
          var noun = kind === "groups" ? (total === 1 ? "group" : "groups") : (total === 1 ? "member" : "members");
          if (total > 0) {
            $status.text(total + " " + noun);
          } else {
            $status.text("No " + noun + " match your search.");
          }

          // 2. Render cards with fade effect
          $results.fadeOut(150, function () {
            if (data.html && data.html.trim().length > 0) {
              $results.html(data.html);
            } else {
              $results.html('<div class="col-12 text-center py-5"><p class="h4 text-muted font-weight-normal">No ' + noun + ' match your search.</p></div>');
            }
            $results.fadeIn(150);

            // Re-run effects and AOS
            if (typeof AOS !== "undefined") {
              AOS.refresh();
            }
            if (window.initPublicEffects) {
              window.initPublicEffects($results);
            }
          });

          // 3. Pagination & history URL
          renderPagination(data.page, data.total_pages);
          updateBrowserUrl();
        })
        .fail(function () {
          if (requestId === currentRequestId) {
            $("#directory-status").text("Could not load results. Please try again.");
          }
        });
    }

    function onFilterChange(resetPage) {
      if (resetPage) {
        page = 1;
      }
      q = $("#filter-q").val() || "";
      if (kind === "groups") {
        tagOrSkill = $("#filter-tag").val() || "";
      } else {
        tagOrSkill = $("#filter-skill").val() || "";
        group = $("#filter-group").val() || "";
      }

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        fetchResults();
      }, 250);
    }

    // Bind event listeners
    $("#filter-q").on("keyup input", function () {
      onFilterChange(true);
    });

    if (kind === "groups") {
      $("#filter-tag").on("keyup input", function () {
        onFilterChange(true);
      });
    } else {
      $("#filter-skill").on("keyup input", function () {
        onFilterChange(true);
      });
      $("#filter-group").on("change", function () {
        onFilterChange(true);
      });
    }

    // Pagination click handler
    $(document).on("click", "#directory-pagination .js-page-link", function (e) {
      e.preventDefault();
      var targetPage = parseInt($(this).data("page"), 10);
      if (targetPage && targetPage !== page) {
        page = targetPage;
        fetchResults();
        $("html, body").stop().animate({
          scrollTop: $("#directory-filter").offset().top - 80
        }, 300);
      }
    });
  });
})(jQuery);
