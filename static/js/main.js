$(document).ready(function() {
    const modalContainer = $('#modal-container');
    const modalContent = $('#modal-content');
    const modalBody = $('#modal-body');
    const closeModalBtn = $('#close-modal-btn');

    // --- A. Handle Opening the Modal ---
    $(document).on('click', '.modal-trigger', function() {
        const url = $(this).data('modal-url');

        modalBody.html('<p style="text-align: center; padding: 20px;">Loading form...</p>');
        modalContainer.show(); 
        modalContent.hide().fadeIn(150); 

        $.get(url, function(data) {
            // If the "form" returned is actually the full index page HTML, redirect
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
                window.location.href = "/"; // Redirect if unauthorized
                return;
            }
            if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                errorMsg = jqXHR.responseJSON.error;
            }
            modalBody.html(`<p style="color: red; padding: 20px; text-align: center;">${errorMsg}</p>`);
        });
    });

    // --- B. Handle Closing the Modal ---
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

    // --- C. Handle Form Submission (AJAX POST) ---
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
                // If response is the Success JSON
                if (response.success) {
                    location.reload(); 
                } 
                // If Flask redirected to Index (HTML string), force full page reload
                else if (typeof response === 'string' && response.includes('<!DOCTYPE html>')) {
                    window.location.href = "/";
                }
            },
            error: function(jqXHR) {
                // If server returns 403 (Forbidden), redirect the whole window
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
                } 
                else if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                    errorHtml += `<li style="color: red;">${jqXHR.responseJSON.error}</li>`;
                } 
                else {
                    errorHtml += '<li style="color: red;">An unexpected error occurred.</li>';
                }
                
                errorHtml += '</ul>';
                errorDiv.html(errorHtml);
            }
        });
    });
});