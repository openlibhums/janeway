/**
 * Handles the enlargement of tables in article templates.
 * Theme configurations passed from article template.
 * modalSelector - varies by theme, e.g. modal, reveal
 * linkTemplate - varies by theme - different classes etc.
 * 
 * note: table-label is a class name set by xsl used here to create a unique heading for each modal.
 */

function initTableExpansion(config) {

    function addExpansionLinks(){
        $('.table-expansion').each(function() {
            var $table = $(this);
            var tableId = $table.attr('id');
            
            // Don't add them to the modal version
            if (!$table.closest(config.modalSelector).length) {
                var $child = $table.children(":first");
                
                // Don't duplicate
                var existingLink = $child.find('a[href^="#table-"], button[data-target^="#table-"], a[data-open^="table-"]');
                if (!existingLink.length) {
                    $child.append(config.linkTemplate.replace('{id}', tableId));
                }
            }
        });
    }
    
    function createModalHeading(){
        $(config.modalSelector).each(function() {
            var $modal = $(this);
            $modal.find('span.table-label').each(function() {
                var $span = $(this);
                var $h2 = $('<h2>').text($span.text());
                
                // Copy all attributes from span to h2
                $.each($span[0].attributes, function() {
                    $h2.attr(this.name, this.value);
                });
                
                $span.replaceWith($h2);
            });
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

    addExpansionLinks();
    createModalHeading();
    pageLinksCloseModal()
} 