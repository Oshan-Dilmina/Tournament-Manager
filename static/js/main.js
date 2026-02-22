// static/js/main.js

$(document).ready(function() {
    // Select essential DOM elements
    const modalContainer = $('#modal-container'); // The background overlay
    const modalContent = $('#modal-content');     // The inner box
    const modalBody = $('#modal-body');           // Where the form HTML is inserted
    const closeModalBtn = $('#close-modal-btn');  // The close button (X)

    // --- A. Handle Opening the Modal ---
    // Listens for clicks on any element with the class 'modal-trigger'
    $(document).on('click', '.modal-trigger', function() {
        const url = $(this).data('modal-url'); // Get the URL from the button's data attribute

        // 1. Prepare and show the container immediately (Zero lag)
        modalBody.html('<p style="text-align: center; padding: 20px;">Loading form...</p>');
        modalContainer.show(); 
        
        // Smoother look for the inner content
        modalContent.hide().fadeIn(150); 

        // 2. Send AJAX GET request to fetch the form HTML from Flask
        $.get(url, function(data) {
            modalBody.html(data); 
            
            // Auto-focus the first input so the user can start typing immediately
            modalBody.find('input[type="text"], input[type="number"]').first().focus();
        })
        .fail(function(jqXHR) {
            // Handle cases where the Flask route returns 404 or 500
            let errorMsg = 'Error loading form. Please check the server logs.';
            if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                errorMsg = jqXHR.responseJSON.error;
            }
            modalBody.html('<p style="color: red; padding: 20px; text-align: center;">' + errorMsg + '</p>');
        });
    });

    // --- B. Handle Closing the Modal ---
    
    // 1. Close when the 'X' button is clicked
    closeModalBtn.on('click', function() {
        modalContainer.hide();
        modalBody.empty(); // Clear content to reset state
    });

    // 2. Close when the user clicks on the dark background overlay (outside the white box)
    modalContainer.on('click', function(e) {
        if (e.target.id === 'modal-container') {
            modalContainer.hide();
            modalBody.empty();
        }
    });

    // --- C. Handle Form Submission (AJAX POST) ---
    // Using a class (.ajax-form) instead of an ID (#ajax-form) prevents conflicts
    $(document).on('submit', '.ajax-form', function(e) {
        e.preventDefault();
    
        // $(this) refers specifically to the form currently being submitted
        const form = $(this);
        const errorDiv = form.find('#form-errors'); 
        errorDiv.empty();
        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                if (response.success) {
                    // Refresh the page to reflect the database changes (New Player/Team/Edit)
                    location.reload(); 
                }
            },
            error: function(jqXHR) {
                // FAILURE: Flask route returned HTTP 400 (Validation) or 500 (Server Error)
                let errorHtml = '<ul style="list-style-type: none; padding: 0; margin-bottom: 10px;">';
                
                if (jqXHR.status === 400 && jqXHR.responseJSON && jqXHR.responseJSON.errors) {
                    // Validation Errors from Flask-WTF (e.g., Score cannot be empty)
                    for (let field in jqXHR.responseJSON.errors) {
                        jqXHR.responseJSON.errors[field].forEach(error => {
                            // Capitalize the field name for display
                            const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
                            errorHtml += `<li style="color: red;"><strong>${fieldName}</strong>: ${error}</li>`;
                        });
                    }
                } 
                else if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                    // Custom error messages sent from Flask via jsonify({'error': '...'})
                    errorHtml += `<li style="color: red;">${jqXHR.responseJSON.error}</li>`;
                } 
                else {
                    // Generic fallback for network issues or unhandled exceptions
                    errorHtml += '<li style="color: red;">An unexpected error occurred. Please try again.</li>';
                }
                
                errorHtml += '</ul>';
                errorDiv.html(errorHtml);
            }
        });
    });
});