let sidebar = document.getElementById('sidebar');
let team_logo = document.getElementById('team_logo');
let panel_title = document.getElementById('panel_title');
let status_detector = document.getElementById('status_detector');
let nav_link = document.getElementsByClassName('nav-link');

sidebar.addEventListener('click', (event) => {
    // Check if the clicked element is the sidebar or its immediate children
    if (event.target === sidebar || sidebar.contains(event.target)) {
        // Check if the clicked element is one of the immediate children of the sidebar
        if (event.target !== sidebar) {
            return; // Do nothing if clicked on a child element
        }
        
        sidebar.style.transition = '0.5s';
        if (sidebar.id === 'shrinked-sidebar') {
            sidebar.id = 'sidebar';
            team_logo.style.width = '150px';
            document.body.style.marginLeft = '180px'; // pushes the body to the right for the sidebar
            team_logo.style.height = '150px';
            panel_title.style.display = 'block';
            status_detector.style.marginTop = '0';
            for (let i = 0; i < nav_link.length; i++) {
                nav_link[i].style.fontSize = '20px';
            }
        } else if (sidebar.id === 'sidebar') {
            // shrink the body to the left when the sidebar is shrinked
            document.body.style.marginLeft = '80px';
            sidebar.id = 'shrinked-sidebar';
            team_logo.style.width = '70px';
            team_logo.style.height = '70px';
            panel_title.style.display = 'none';
            status_detector.style.marginTop = '20px';
            for (let i = 0; i < nav_link.length; i++) {
                nav_link[i].style.fontSize = '0px';
            }
        }
    }
});

