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
        html += '<li class="page-item"><a class="page-link text-warning js-page-link" style="background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; margin: 0 3px;" href="#" data-page="' + (currentPage - 1) + '">&laquo; Prev</a></li>';
      } else {
        html += '<li class="page-item disabled"><span class="page-link text-muted" style="background: rgba(17, 24, 39, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 6px; margin: 0 3px;">&laquo; Prev</span></li>';
      }

      // Pages
      for (var p = 1; p <= totalPages; p++) {
        if (p === currentPage) {
          html += '<li class="page-item active"><span class="page-link bg-warning text-dark border-warning font-weight-bold" style="border-radius: 6px; margin: 0 3px;">' + p + '</span></li>';
        } else {
          html += '<li class="page-item"><a class="page-link text-light js-page-link" style="background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; margin: 0 3px;" href="#" data-page="' + p + '">' + p + '</a></li>';
        }
      }

      // Next
      if (currentPage < totalPages) {
        html += '<li class="page-item"><a class="page-link text-warning js-page-link" style="background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; margin: 0 3px;" href="#" data-page="' + (currentPage + 1) + '">Next &raquo;</a></li>';
      } else {
        html += '<li class="page-item disabled"><span class="page-link text-muted" style="background: rgba(17, 24, 39, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 6px; margin: 0 3px;">Next &raquo;</span></li>';
      }

      html += '</ul>';
      $nav.html(html);
    }

    function fetchResults() {
      var requestId = ++currentRequestId;
      var params = buildUrlParams();
      var $results = $("#directory-results");
      var $status = $("#directory-status");

      $results.css("opacity", "0.55");

      $.getJSON(endpoint + "?" + params.toString())
        .done(function (data) {
          if (requestId !== currentRequestId) {
            return; // Ignore stale responses
          }

          var total = data.total_count || 0;
          var noun = kind === "groups" ? (total === 1 ? "group" : "groups") : (total === 1 ? "member" : "members");
          if (total > 0) {
            $status.text(total + " " + noun);
          } else {
            $status.text("No " + noun + " match your search.");
          }

          // Render cards with fade effect
          $results.fadeOut(150, function () {
            if (data.html && data.html.trim().length > 0) {
              $results.html(data.html);
            } else {
              $results.html('<div class="col-12 text-center py-5 cc-hud-tile my-3"><p class="h4 text-muted font-weight-normal mb-0">No ' + noun + ' match your search.</p></div>');
            }
            $results.css("opacity", "1").fadeIn(150);

            // Re-run effects and AOS
            if (typeof AOS !== "undefined") {
              AOS.refresh();
            }
            if (window.initPublicEffects) {
              window.initPublicEffects($results);
            }
          });

          // Pagination & history URL
          renderPagination(data.page, data.total_pages);
          updateBrowserUrl();
        })
        .fail(function () {
          if (requestId === currentRequestId) {
            $results.css("opacity", "1");
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
      debounceTimer = setTimeout(fetchResults, 250);
    }

    // Input event listeners
    $("#filter-q").on("input", function () {
      onFilterChange(true);
    });

    if (kind === "groups") {
      $("#filter-tag").on("input", function () {
        onFilterChange(true);
      });
    } else {
      $("#filter-skill").on("input", function () {
        onFilterChange(true);
      });
      $("#filter-group").on("change", function () {
        onFilterChange(true);
      });
    }

    // Delegated pagination click
    $(document).on("click", "#directory-pagination .js-page-link", function (e) {
      e.preventDefault();
      var targetPage = parseInt($(this).data("page"), 10);
      if (targetPage && targetPage !== page) {
        page = targetPage;
        fetchResults();
        $("html, body").animate({
          scrollTop: $("#directory-filter").offset().top - 90
        }, 300);
      }
    });

    // Handle browser back/forward buttons
    window.addEventListener("popstate", function () {
      var poppedParams = new URLSearchParams(window.location.search);
      q = poppedParams.get("q") || "";
      tagOrSkill = kind === "groups" ? (poppedParams.get("tag") || "") : (poppedParams.get("skill") || "");
      group = poppedParams.get("group") || "";
      page = parseInt(poppedParams.get("page"), 10) || 1;

      $("#filter-q").val(q);
      if (kind === "groups") {
        $("#filter-tag").val(tagOrSkill);
      } else {
        $("#filter-skill").val(tagOrSkill);
        $("#filter-group").val(group);
      }

      fetchResults();
    });
  });
})(jQuery);
