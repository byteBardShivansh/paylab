/**
 * Simple frontend JavaScript for testing the Payments API
 * 
 * This script handles form submission and API communication
 * for the FastAPI payments microservice.
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const PAYMENTS_ENDPOINT = '/payments';

// Global variable to store API key (can be set from environment or prompt)
let apiKey = null;

/**
 * Get API key from localStorage, environment, or prompt user
 * @returns {string} The API key to use for requests
 */
function getApiKey() {
    // First check if we already have it in memory
    if (apiKey) {
        return apiKey;
    }
    
    // Check localStorage for previously saved key
    const savedKey = localStorage.getItem('payments_api_key');
    if (savedKey) {
        apiKey = savedKey;
        return apiKey;
    }
    
    // Prompt user for API key
    const userKey = prompt('Please enter your API key:');
    if (userKey) {
        apiKey = userKey.trim();
        // Save to localStorage for future use
        localStorage.setItem('payments_api_key', apiKey);
        return apiKey;
    }
    
    return null;
}

/**
 * Clear stored API key (useful for testing different keys)
 */
function clearApiKey() {
    apiKey = null;
    localStorage.removeItem('payments_api_key');
}

/**
 * Display response in the response area
 * @param {Object} response - The response data to display
 * @param {boolean} isSuccess - Whether this is a success or error response
 */
function displayResponse(response, isSuccess = true) {
    const responseArea = document.getElementById('responseArea');
    const responseContent = document.getElementById('responseContent');
    
    // Show the response area
    responseArea.style.display = 'block';
    
    // Apply appropriate styling
    responseArea.className = `response ${isSuccess ? 'success' : 'error'}`;
    
    // Format and display the response
    responseContent.textContent = JSON.stringify(response, null, 2);
    
    // Scroll to response
    responseArea.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Handle form submission
 * @param {Event} event - The form submission event
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const formData = new FormData(event.target);
    const paymentData = {
        order_id: formData.get('order_id'),
        amount: parseFloat(formData.get('amount')),
        currency: formData.get('currency')
    };
    
    // Get API key
    const key = getApiKey();
    if (!key) {
        displayResponse({
            error: 'API key required',
            message: 'Please provide a valid API key to use this service'
        }, false);
        return;
    }
    
    // Get submit button and show loading state
    const submitButton = event.target.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Creating Payment...';
    
    try {
        // Make API request
        const response = await fetch(`${API_BASE_URL}${PAYMENTS_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': key
            },
            body: JSON.stringify(paymentData)
        });
        
        // Parse response
        const responseData = await response.json();
        
        if (response.ok) {
            // Success response
            displayResponse({
                status: response.status,
                statusText: response.statusText,
                data: responseData
            }, true);
        } else {
            // Error response
            displayResponse({
                status: response.status,
                statusText: response.statusText,
                error: responseData
            }, false);
        }
        
    } catch (error) {
        // Network or other errors
        displayResponse({
            error: 'Network Error',
            message: error.message,
            details: 'Check if the API server is running at ' + API_BASE_URL
        }, false);
    } finally {
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    }
}

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the payment form
    const form = document.getElementById('paymentForm');
    
    // Add form submission handler
    form.addEventListener('submit', handleFormSubmit);
    
    // Add some helpful functions to the global scope for testing/debugging
    window.paymentsDebug = {
        clearApiKey: clearApiKey,
        setApiKey: function(key) {
            apiKey = key;
            localStorage.setItem('payments_api_key', key);
        },
        getApiKey: getApiKey,
        testConnection: async function() {
            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();
                console.log('API Health Check:', data);
                return data;
            } catch (error) {
                console.error('API Health Check Failed:', error);
                return null;
            }
        }
    };
    
    console.log('Payments frontend initialized');
    console.log('Debug functions available at window.paymentsDebug');
});