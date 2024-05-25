document.getElementById('login_form').addEventListener('submit', requestLogin);

let notif_ribbon = document.getElementById('notif_ribbon'); // A div element to display notifications

function ribbon_alert (message, colour) {
    // Sets the HTML and CSS of the notification ribbon depending on the response
    notif_ribbon.innerHTML = message;
    notif_ribbon.style.display = 'block';
    notif_ribbon.style.backgroundColor = colour || '#d07f7f';
    notif_ribbon.style.color = 'white';
    notif_ribbon.style.padding = '5px';
    notif_ribbon.style.margin = '5px';
    notif_ribbon.style.borderRadius = '5px';
    notif_ribbon.style.border = 'var(--bs-border-width) solid var(--bs-border-color);';
    notif_ribbon.style.boxShadow = 'inset 0 1px 1px rgba(0,0,0,.075),0 0 8px rgb(104, 145, 162)';
    notif_ribbon.style.boxSizing = 'border-box';
    notif_ribbon.style.maxHeight = '100px';
    notif_ribbon.style.maxWidth = '80vw';
    notif_ribbon.style.overflowX = 'hidden';
    notif_ribbon.style.overflowY = 'scroll';
}

// Listen for click event on the "Register account" button
document.getElementById('register_button').addEventListener('click', function(event) {
    // Set the value of the hidden input field 'do_register' to 'true'
    document.querySelector('input[name="do_register"]').value = 'true';
});

function requestLogin(event) {
    event.preventDefault();
    var form = event.target; // Get the form that triggered the event
    var formData = new FormData(form);
    var response_ok = null;

    fetch('http://127.0.0.1:5005/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email_address: formData.get('email_address'),
            password: formData.get('password'),
            is_registering: formData.get('do_register') === 'true', // Convert string to boolean
        })
    })
    .then(response => {
        response_ok = response.ok;
        return response.json();
    })
    .then(data => {
        if (response_ok) {
            // Sets the token in the local storage
            localStorage.setItem('token', data['token']);
            ribbon_alert('Login successful. Sending you to the home page.', 'green');
            window.location.href = '/index.html';    
        } else {
            ribbon_alert(data['message']);
        }
    });
}