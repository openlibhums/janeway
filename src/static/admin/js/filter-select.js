/*
 * Replaces the <select> of each .filter-select with an ARIA combobox that
 * filters its options. The hidden <select> still holds the submitted value.
 */
(function () {
  var counter = 0;

  function initFilterSelect(container) {
    if (container.dataset.filterSelectReady) {
      return;
    }
    container.dataset.filterSelectReady = "true";

    var select = container.querySelector("select");
    var id = "filter-select-" + (++counter);
    var input = document.createElement("input");
    var listbox = document.createElement("ul");
    var matches = [];
    var activeIndex = -1;

    input.type = "text";
    input.id = id + "-input";
    input.className = "filter-select-input";
    input.placeholder = container.dataset.placeholder || "";
    input.autocomplete = "off";
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-controls", id + "-listbox");

    listbox.id = id + "-listbox";
    listbox.className = "filter-select-listbox";
    listbox.setAttribute("role", "listbox");
    listbox.hidden = true;

    var label = container.querySelector("label");
    if (label) {
      label.htmlFor = input.id;
      listbox.setAttribute("aria-label", label.textContent.trim());
    }

    select.hidden = true;
    select.tabIndex = -1;
    container.insertBefore(input, select);
    container.insertBefore(listbox, select);

    function selectedOption() {
      return select.options[select.selectedIndex];
    }

    function resetText() {
      var option = selectedOption();
      input.value = option ? option.text : "";
    }

    function position() {
      // Fixed so that scrolling tables do not clip the list
      var rect = input.getBoundingClientRect();
      listbox.style.top = rect.bottom + "px";
      listbox.style.left = rect.left + "px";
      listbox.style.minWidth = rect.width + "px";
    }

    function setActive(index) {
      var items = listbox.querySelectorAll('[role="option"]');
      items.forEach(function (item) { item.classList.remove("is-active"); });
      if (index < 0 || index >= items.length) {
        activeIndex = -1;
        input.removeAttribute("aria-activedescendant");
        return;
      }
      activeIndex = index;
      items[index].classList.add("is-active");
      input.setAttribute("aria-activedescendant", items[index].id);
      items[index].scrollIntoView({ block: "nearest" });
    }

    function render(query) {
      query = (query || "").trim().toLowerCase();
      listbox.innerHTML = "";
      matches = Array.prototype.filter.call(select.options, function (option) {
        return !query || option.text.toLowerCase().indexOf(query) !== -1;
      });
      matches.forEach(function (option, index) {
        var item = document.createElement("li");
        item.id = id + "-option-" + index;
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", option.selected ? "true" : "false");
        item.textContent = option.text;
        // mousedown fires before the input loses focus
        item.addEventListener("mousedown", function (event) {
          event.preventDefault();
          choose(option);
        });
        listbox.appendChild(item);
      });
      if (!matches.length) {
        var empty = document.createElement("li");
        empty.className = "filter-select-empty";
        empty.textContent = container.dataset.noMatches || "";
        listbox.appendChild(empty);
      }
      var selectedIndex = matches.indexOf(selectedOption());
      setActive(query ? 0 : selectedIndex);
    }

    function open(query) {
      render(query);
      position();
      listbox.hidden = false;
      input.setAttribute("aria-expanded", "true");
      window.addEventListener("scroll", onScroll, true);
      window.addEventListener("resize", position);
    }

    function close() {
      listbox.hidden = true;
      input.setAttribute("aria-expanded", "false");
      setActive(-1);
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", position);
    }

    function onScroll(event) {
      if (event.target !== listbox) {
        position();
      }
    }

    function choose(option) {
      select.value = option.value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      resetText();
      close();
    }

    input.addEventListener("focus", function () {
      input.select();
      open("");
    });
    input.addEventListener("click", function () {
      if (listbox.hidden) {
        open("");
      }
    });
    input.addEventListener("input", function () {
      open(input.value);
    });
    input.addEventListener("blur", function () {
      resetText();
      close();
    });
    input.addEventListener("keydown", function (event) {
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          if (listbox.hidden) {
            open("");
          } else {
            setActive(Math.min(activeIndex + 1, matches.length - 1));
          }
          break;
        case "ArrowUp":
          event.preventDefault();
          setActive(Math.max(activeIndex - 1, 0));
          break;
        case "Enter":
          event.preventDefault();
          if (!listbox.hidden && matches[activeIndex]) {
            choose(matches[activeIndex]);
          }
          break;
        case "Escape":
          if (!listbox.hidden) {
            event.preventDefault();
            resetText();
            close();
          }
          break;
      }
    });

    resetText();
  }

  function initAll(root) {
    (root || document).querySelectorAll(".filter-select").forEach(initFilterSelect);
  }

  if (window.htmx) {
    htmx.onLoad(initAll);
  } else {
    document.addEventListener("DOMContentLoaded", function () { initAll(); });
  }
})();
