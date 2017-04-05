/*!
 * UCSC Genomics Institute - CGL
 * https://cgl.genomics.ucsc.edu/
 *
 * Lightweight menu toggle, show/hide menu associated with hamburger. Small and extra small devices only.
 */

(function() {

    "use strict";

    /**
     * CC hamburger/full screen nav module.
     *
     * @returns {Object} Public API of CGL website.
     */
    var CGL_HAMBURGER = (function() {

        // Locals
        var CSS_NAVBAR_OPEN = "toolbar-menu-open";
        var MENU_OPEN_TOGGLE = "[menu-open]";
        var MENU_CLOSE_TOGGLE = "[menu-close]";

        /**
         * PUBLIC API
         */
        return {

            // Called on page load to set up hamburger
            init: init
        };

        /**
         * PRIVATES
         */

        /**
         * Prevent scroll when menu is open. Touch devices only - non-touch devices use overflow CSS property to
         * control scroll.
         *
         * @param bodyEl {Element}
         */
        function disableScroll(bodyEl) {

            bodyEl.addEventListener("touchmove", scrollFn);
        }

        /**
         * Enable click handler to close menu on click of menu item.
         *
         * @param bodyEl {Element}
         */
        function enableClickToClose(bodyEl) {

            var menuCloseEl = bodyEl.querySelectorAll(MENU_CLOSE_TOGGLE)[0];
            if ( !menuCloseEl ) {
                return;
            }

            // Set up click event on hamburger toggle
            menuCloseEl.addEventListener("click", onClickMenuClose);
        }

        /**
         * Enable scroll when menu is closed.
         *
         * @param bodyEl {Element}
         */
        function enableScroll(bodyEl) {

            bodyEl.removeEventListener("touchmove", scrollFn);
        }

        /**
         * Hide menu.
         *
         * @param body {Element}
         */
        function hideMenu(bodyEl) {

            // Toggle visibility of menu
            bodyEl.classList.remove(CSS_NAVBAR_OPEN);
        }

        /**
         * Set up components, state, data
         */
        function init() {

            // Set up hamburger/menu toggle
            initHamburger();
        }

        /**
         * Add/remove class on body to toggle visibility of nav menu on mobile.
         *
         * Also prevent scroll if menu is open. This is specifically for touch devices where overflow: hidden on body
         * is not obeyed. https://worldvectorlogo.com/logos/obey.svg
         */
        function initHamburger() {

            // Set up hamburger toggle - grab a handle on the toggle element
            var menuOpenEl = document.querySelectorAll(MENU_OPEN_TOGGLE)[0];
            if ( !menuOpenEl ) {
                return;
            }

            // Set up click event on hamburger toggle
            menuOpenEl.addEventListener("click", onClickMenuOpen);
        }

        /**
         * Click handler, registered on menu close element
         *
         * @param evt {Event}
         */
        function onClickMenuClose(evt) {

            // Mind you own business!
            evt.preventDefault();

            // Close menu
            var bodyEl = document.body;
            hideMenu(bodyEl);

            // Enable scroll
            enableScroll(bodyEl);
        }

        /**
         * Click handler, registered on hamburger element
         *
         * @param evt {Event}
         */
        function onClickMenuOpen(evt) {

            // Mind you own business!
            evt.preventDefault();

            // Open menu
            var bodyEl = document.body;
            showMenu(bodyEl);

            // Disable scroll
            disableScroll(bodyEl);
        }

        /**
         * Scroll (touchmove) event handler function - needs to be individual function so we can bind and unbind
         * depending on open/closed state of menu.
         *
         * @param evt {Event}
         */
        function scrollFn(evt) {

            evt.preventDefault();
        }

        /**
         * Show menu.
         *
         * @param bodyEl {Element}
         */
        function showMenu(bodyEl) {

            // Toggle visibility of menu
            bodyEl.classList.add(CSS_NAVBAR_OPEN);

            // Enable click to close menu
            enableClickToClose(bodyEl);
        }
    })();

    // Kick off initialization of hamburger...
    CGL_HAMBURGER.init();

})();


