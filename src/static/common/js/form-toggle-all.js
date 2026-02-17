/**
 * Initialize a pair of select all and clear all form buttons.
 *
 * Usage:
 *   - call initFormToggleButtons(selectAllButtonId, clearAllButtonId, formId) programmatically
 * 
 * @param {string} selectAllButtonId - ID of the select all button
 * @param {string} clearAllButtonId - ID of the clear all button
 * @param {string} formId - ID of the form
 */
function initFormToggleButtons(selectAllButtonId, clearAllButtonId, formId) {
    console.log("init")
    const selectAllButton = document.getElementById(selectAllButtonId);
    const clearAllButton = document.getElementById(clearAllButtonId);
    const form = document.getElementById(formId);
    console.log(selectAllButton);
    console.log(clearAllButton);
    console.log(form);
    
    if (!selectAllButton || !clearAllButton || !form) {
        console.warn('FormToggleButtons: Button or form not found', { 
            selectAllButtonId, 
            clearAllButtonId, 
            formId 
        });
        return;
    }
    
    function enableButtons() {
        console.log("enable")
        selectAllButton.disabled = false;
        clearAllButton.disabled = false;
    }
    
    // When form changes, both select all and clear all buttons could have an impact, and so should be enabled
    const formInputs = form.querySelectorAll('input, select, textarea');
    formInputs.forEach(function(input) {
        input.addEventListener('change', enableButtons);
        input.addEventListener('input', enableButtons);
    });
    
    // Select all button click handler
    selectAllButton.addEventListener('click', function() {
        console.log("select");
        // Select all checkboxes
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = true;
        });
        
        // All now selected, so disable this button and enable the clear all button
        selectAllButton.disabled = true;
        clearAllButton.disabled = false;
    });
    
    // Clear all button click handler
    clearAllButton.addEventListener('click', function() {
        console.log("clear")
        // Clear all checkboxes
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = false;
        });
        
        // Clear text inputs, selects, and other form elements
        const textInputs = form.querySelectorAll('input[type="text"], input[type="search"], input[type="email"], input[type="number"], textarea');
        textInputs.forEach(function(input) {
            input.value = '';
        });
        
        // Clear select dropdowns
        const selects = form.querySelectorAll('select');
        selects.forEach(function(select) {
            select.selectedIndex = -1;
        });
        
        // All now cleared, so disable this button and enable the select all button
        clearAllButton.disabled = true;
        selectAllButton.disabled = false;
    });
}
