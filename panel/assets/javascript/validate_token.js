function kickUser () {
    window.location.href = '/login.html';
}

function validateToken() {
    let token = localStorage.getItem('token');
    // Checks to see if the page is login.html, returns if it is
    if (window.location.href.includes('login.html')) {
        console.log('login.html. Exiting validateToken()')
        return;
    }

    // Continually pings the server to check if the token is still valid    
    fetch('http://127.0.0.1:5005/api/validate_token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            token: token
        })
    })
    .then(response => {
        return response.text(); // Parse response body as text
    })
    .then(data => {
        if (data !== 'ok') { // Check if response indicates session is not valid
            // If the page == login.html, alert the user that their session has expired and redirect them to the login page
            kickUser();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while validating your session. Please log in again.');
        kickUser();
    });
}

// Runs every once in a while to check if the token is still valid if the user is not on the login page
if (!window.location.href.includes('login.html')) {  
    validateToken();
    setInterval(validateToken, 10000);
}