/**
 * Handles the enlargement of tables in article templates.
 * Theme configurations passed from article template.
 * modalSelector - varies by theme, e.g. modal, reveal
 * linkTemplate - varies by theme - different classes etc.
 * materializeWorkarounds - work arounds for material (set as true to use it) - fixes a11y issues on open and close.
 * 
 * note: table-label is a class name set by xsl used here to create a unique heading for each modal.
 */

function initTableExpansion(config) {

    // Counter for generic table headings when no span.table-label exists
    var genericTableCounter = 1;

    function addExpansionLinks(){
        $('.table-expansion').each(function() {
            var $table = $(this);
            var tableId = $table.attr('id');
            
            // Don't add them to the modal version
            if (!$table.closest(config.modalSelector).length) {
                var $child = $table.children(":first");
                
                // Don't duplicate
                var existingLink = $child.find('a[href^="#table-"], button[data-target^="#table-"], button[data-open^="table-"]');
                if (!existingLink.length) {
                    $child.append(config.linkTemplate.replace(/{id}/g, tableId));
                }
            }
        });
    }
    
    function createTableModalHeading(){
        $(config.modalSelector).each(function() {
            var $modal = $(this);
            var $tableLabels = $modal.find('span.table-label');
            
            if ($tableLabels.length >= 1) {
                console.log('opt1');
                // First table-label is used as an h2 for the modal
                var $span = $tableLabels.first();
                var $h2 = $('<h2>').text($span.text());
                
                // Copy all attributes from span to h2
                $.each($span[0].attributes, function() {
                    $h2.attr(this.name, this.value);
                });
                
                $span.replaceWith($h2);
                
            } else {
                console.log('opt2');
                console.log($modal)
                // Case 3: create generic h2 when no table-label exists
                var $h2 = $('<h2>').text('Table ' + genericTableCounter);
                $modal.prepend($h2);
                genericTableCounter++;
            }
        });
    }

    function pageLinksCloseModal(){
        $(document).on('click', config.modalSelector + ' a[href^="#"]', function(e) {
            var $link = $(this);
            var href = $link.attr('href');
            var $modal = $link.closest(config.modalSelector);
            
            if ($modal.length) {
                // Check if the target element is within the same modal
                var targetId = href.substring(1);
                var $target = $('#' + targetId);
                
                // Only close the modal if the target is outside of it
                if (!$target.length || !$modal.find('#' + targetId).length) {
                    // Close the modal using the appropriate method based on the framework
                    if ($modal.hasClass('modal') || $modal.hasClass('fade')) {//olh
                        $modal.modal('hide');
                    } else if ($modal.hasClass('reveal')) {//clean and material
                        $modal.foundation('close');
                    }
                }
                
                // Let the default navigation happen naturally
            }
        });
    }

    function handleModalFocusManagement() {
        var triggerElement = null;
        $(document).on('click', '.modal-trigger', function(e) {
            triggerElement = this;
        });

        function closeHandler(){
            if (triggerElement) {
                setTimeout(function() {
                    triggerElement.focus();
                    triggerElement = null;
                }, 100);
            }
        }
        
        // close buttons
        $(document).on('click', '[data-dismiss="modal"]', function(e) {
            closeHandler();
        });
        $(document).on('click', '.modal-close', function(e) {
            closeHandler();
        });
        $(document).on('modal:close', function(e) {
            closeHandler();
        });

        // Click outside the modal
        $(document).on('click', '.modal-overlay', function(e) {
            closeHandler();
        });
        $(document).on('click', '.modal-backdrop', function(e) {
            closeHandler();
        });
        
        //ESC key
        $(document).on('keydown', function(e) {
            if (e.keyCode === 27) { // ESC key
                var $openModal = $('.modal.open');
                if ($openModal.length) {
                    closeHandler();
                }
            }
        });
    }

    // accessibility workaround for material
    function handleModalScrollToTop() {
        $(document).on('DOMNodeInserted', function(e) {
            if ($(e.target).hasClass('modal') && $(e.target).hasClass('open')) {
                setTimeout(function() {
                    $(e.target).scrollTop(0);
                    var $h2 = $(e.target).find('h2').first();
                    if ($h2.length) {
                        $h2.attr('tabindex', '-1');
                        // Let Materialize focus the close button first, then move to h2
                        setTimeout(function() {
                            $h2.focus();
                        }, 50);
                    }
                }, 200);
            }
            console.log("focus");
        });
    }

    addExpansionLinks();
    createTableModalHeading();
    pageLinksCloseModal();
    
    // Only handle custom focus management if on materialize
    if (config.materializeWorkarounds) {
        handleModalScrollToTop();
        handleModalFocusManagement();
    }
} 