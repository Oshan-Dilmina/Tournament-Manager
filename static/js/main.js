$(document).ready(function() {
    const modalContainer = $('#modal-container');
    const modalContent = $('#modal-content');
    const modalBody = $('#modal-body');
    const closeModalBtn = $('#close-modal-btn');

    // --- 1. Tournament UI Logic (New) ---

    // Toggle Blue Border for the "Record Player" Switch
    window.updateRecordBorder = function() {
        const checkbox = $('#record_player');
        const container = $('#record-player-container');
        const typeSelect = $('#type');

        if (checkbox.length && container.length) {
            const isTeamed = typeSelect.length ? typeSelect.val() === 'teamed' : true;

            if (isTeamed && checkbox.is(':checked')) {
                container.addClass('active-blue-border shadow-sm');
            } else {
                container.removeClass('active-blue-border shadow-sm');
            }
        }
    };

    // Enable/Disable "Record Player" based on Tournament Type
    window.checkTeamedStatus = function() {
        const typeSelect = $('#type');
        const recordContainer = $('#record-player-container');
        const recordCheckbox = $('#record_player');
        
        if (!typeSelect.length || !recordContainer.length || !recordCheckbox.length) return;

        if (typeSelect.val() === 'teamed') {
            recordContainer.css('opacity', '1');
            recordCheckbox.prop('disabled', false);
            updateRecordBorder();
        } else {
            recordContainer.css('opacity', '0.5');
            recordContainer.removeClass('active-blue-border shadow-sm');
            recordCheckbox.prop('checked', false);
            recordCheckbox.prop('disabled', true);
        }
    };

    // Toggle Blue Border and Settings for Scoring System
    window.toggleMarginSettings = function(isMargin) {
        const marginContainer = $('#margin-container');
        const classicContainer = $('#classic-container');
        const marginSettings = $('#margin-settings');

        if (!marginContainer.length || !classicContainer.length) return;

        if (isMargin) {
            marginContainer.addClass('active-blue-border shadow-sm').css('background-color', '#f8fbff');
            if (marginSettings.length) marginSettings.show();
            
            classicContainer.removeClass('active-blue-border shadow-sm').css('background-color', 'transparent');
        } else {
            classicContainer.addClass('active-blue-border shadow-sm').css('background-color', '#f8fbff');
            
            marginContainer.removeClass('active-blue-border shadow-sm').css('background-color', 'transparent');
            if (marginSettings.length) marginSettings.hide();
        }
    };

    // --- 2. Handle Opening the Modal (Existing) ---
    $(document).on('click', '.modal-trigger', function() {
        const url = $(this).data('modal-url');

        modalBody.html('<p style="text-align: center; padding: 20px;">Loading form...</p>');
        modalContainer.show(); 
        modalContent.hide().fadeIn(150); 

        $.get(url, function(data) {
            if (typeof data === 'string' && data.includes('<!DOCTYPE html>')) {
                window.location.href = "/";
                return;
            }
            modalBody.html(data); 
            modalBody.find('input[type="text"], input[type="number"]').first().focus();
        })
        .fail(function(jqXHR) {
            let errorMsg = 'Error loading form.';
            if (jqXHR.status === 403 || jqXHR.status === 401) {
                window.location.href = "/";
                return;
            }
            if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                errorMsg = jqXHR.responseJSON.error;
            }
            modalBody.html(`<p style="color: red; padding: 20px; text-align: center;">${errorMsg}</p>`);
        });
    });

    // --- 3. Handle Closing & Submission (Existing) ---
    closeModalBtn.on('click', function() {
        modalContainer.hide();
        modalBody.empty();
    });

    modalContainer.on('click', function(e) {
        if (e.target.id === 'modal-container') {
            modalContainer.hide();
            modalBody.empty();
        }
    });

    $(document).on('submit', '.ajax-form', function(e) {
        e.preventDefault();
        const form = $(this);
        const errorDiv = form.find('#form-errors'); 
        errorDiv.empty();

        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                if (response.success) {
                    location.reload(); 
                } 
                else if (typeof response === 'string' && response.includes('<!DOCTYPE html>')) {
                    window.location.href = "/";
                }
            },
            error: function(jqXHR) {
                if (jqXHR.status === 403 || jqXHR.status === 401) {
                    window.location.href = "/";
                    return;
                }
                let errorHtml = '<ul style="list-style-type: none; padding: 0; margin-bottom: 10px;">';
                if (jqXHR.status === 400 && jqXHR.responseJSON && jqXHR.responseJSON.errors) {
                    for (let field in jqXHR.responseJSON.errors) {
                        jqXHR.responseJSON.errors[field].forEach(error => {
                            const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
                            errorHtml += `<li style="color: red;"><strong>${fieldName}</strong>: ${error}</li>`;
                        });
                    }
                } else if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                    errorHtml += `<li style="color: red;">${jqXHR.responseJSON.error}</li>`;
                } else {
                    errorHtml += '<li style="color: red;">An unexpected error occurred.</li>';
                }
                errorHtml += '</ul>';
                errorDiv.html(errorHtml);
            }
        });
    });

    // --- 4. Initialization ---
    checkTeamedStatus();
    updateRecordBorder();
});