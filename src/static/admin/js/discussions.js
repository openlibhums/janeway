/*
 * Behaviour for the discussion threads admin screens.
 *
 * Everything here is bound once, on page load, using delegated listeners on
 * document.body. The thread list and thread detail are swapped in repeatedly
 * by HTMX, so any script that lived inside those fragments would be evaluated
 * again on every swap and its listeners would accumulate.
 */
(function () {
    if (window.janewayDiscussionsBound) {
        return;
    }
    window.janewayDiscussionsBound = true;

    var HIDDEN_CLASS = "is-hidden";

    function byId(id) {
        return document.getElementById(id);
    }

    function setHidden(element, hidden) {
        if (element) {
            element.classList.toggle(HIDDEN_CLASS, hidden);
        }
    }

    /*
     * Swap between the read only display of a value and the form used to
     * edit it. Both elements are found by a shared key so that the markup
     * only has to carry the key, not a pair of element ids.
     */
    function toggleEdit(key, showForm) {
        var display = byId("discussion-display-" + key);
        var form = byId("discussion-edit-" + key);

        if (!display || !form) {
            return;
        }

        setHidden(display, showForm);
        setHidden(form, !showForm);

        if (showForm) {
            var field = form.querySelector(
                'input:not([type="hidden"]), textarea, select'
            );
            if (field) {
                field.focus();
            }
        } else {
            var trigger = document.querySelector(
                '[data-discussion-edit="' + key + '"]'
            );
            if (trigger) {
                trigger.focus();
            }
        }
    }

    function foundationReveal($modal) {
        if (!$modal.data("zfPlugin")) {
            new Foundation.Reveal($modal);
        }
        return $modal.data("zfPlugin");
    }

    function openInviteModal() {
        var content = byId("invite-modal-content");
        if (content) {
            content.innerHTML = "";
        }

        if (!window.jQuery) {
            return;
        }

        var $modal = window.jQuery("#invite_modal");
        if (!$modal.length) {
            return;
        }

        foundationReveal($modal).open();
    }

    document.body.addEventListener("click", function (event) {
        var target = event.target;
        if (!target || typeof target.closest !== "function") {
            return;
        }

        var editTrigger = target.closest("[data-discussion-edit]");
        if (editTrigger) {
            toggleEdit(editTrigger.getAttribute("data-discussion-edit"), true);
            return;
        }

        var cancelTrigger = target.closest("[data-discussion-cancel]");
        if (cancelTrigger) {
            toggleEdit(
                cancelTrigger.getAttribute("data-discussion-cancel"),
                false
            );
            return;
        }

        if (target.closest("[data-discussion-invite]")) {
            openInviteModal();
        }
    });

    document.body.addEventListener("change", function (event) {
        var input = event.target;
        if (!input || typeof input.closest !== "function") {
            return;
        }
        if (!input.classList.contains("file-attach-input")) {
            return;
        }

        var extras = input.closest(".post-form-extras");
        if (!extras) {
            return;
        }

        var label = extras.querySelector(".file-attach-name");
        if (label) {
            label.textContent =
                input.files && input.files[0] ? input.files[0].name : "";
        }
    });

    document.body.addEventListener("htmx:afterSwap", function (event) {
        var swapped = event.detail && event.detail.target;
        if (!swapped) {
            return;
        }

        if (
            window.jQuery &&
            window.jQuery.fn &&
            window.jQuery.fn.foundation
        ) {
            window.jQuery(swapped).foundation();
        }
    });

    document.body.addEventListener("htmx:responseError", function (event) {
        var xhr = event.detail && event.detail.xhr;
        if (!xhr || typeof toastr === "undefined") {
            return;
        }
        if (xhr.status >= 400 && xhr.status < 500) {
            toastr.error(xhr.responseText || "An error occurred.");
        }
    });
})();
