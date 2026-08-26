/*
FILE PURPOSE: Base project JS — hides the loader, toggles the navbar's
`.scrolled` state, auto-dismisses flash alerts. Extended per milestone,
never replaced.

PROMPT FOR LLM IMPLEMENTATION:
1. Wrap everything in an IIFE taking jQuery as $, "use strict".
2. On $(window).on("load", ...), add the "fadeOut" class to #ftco-loader.
3. Track $(window).scroll to add/remove a "scrolled" class on #ftco-navbar
   once scrollTop() exceeds 150px (Design Plan §2); call the check once
   immediately, in case the page loads already scrolled.
4. After 5 seconds (setTimeout), call .alert("close") on every
   .js-flash-alert element, per PDR §5.1's "auto-dismissing" flash alerts.
5. If window.AOS exists, call AOS.init({ duration: 800, once: true }) —
   guarded so this file doesn't error before AOS's script tag loads on
   templates that don't need it yet.

DEBUGGING:
// console.log("[DEBUG] window load — loader hidden");

OFFLINE DOCKER TEST CASES:
- Simulating a "load" event triggers #ftco-loader to gain the "fadeOut"
  class.
- Setting window scrollTop above 150 and firing "scroll" adds "scrolled"
  to #ftco-navbar; scrolling back to 0 removes it.
*/
