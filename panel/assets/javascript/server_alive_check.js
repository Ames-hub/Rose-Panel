function keepAliveCheck () {
    let status_detector = document.getElementById('status_detector');
    let status_text = document.getElementById('status_text');

    fetch('http://127.0.0.1:5005/api')
        .then(response => response.json())
        .then(data => {
            if (data['status'] == 'ok') {
                status_detector.style.backgroundColor = 'green';
                status_text.innerHTML = 'Online';
            }
            else {
                status_detector.style.backgroundColor = 'red';
                status_text.innerHTML = 'Offline';
            }
        })
        .catch(error => {
            // If it excepts, the server is offline
            status_detector.style.backgroundColor = 'red';
            status_text.innerHTML = 'Offline';
        });
}

keepAliveCheck();
setInterval(keepAliveCheck, 15000);