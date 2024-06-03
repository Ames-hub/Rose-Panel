// SL = Server List
let sl_container = document.getElementById("server_list_container");
const view_all_btn = document.getElementById("view_all_btn");

function addServer (titleText, descText, full_desc, is_online, resource_usage=null) {
    // Adds a <a> element to the server list container
    var server = document.createElement("a");
    server.className = "server";

    // Creates the SVG
    var svg = document.createElement("div");
    // Adds the class 'server_svg' to the SVG
    svg.className = "server_svg";

    // In the element, add a h2 tag title and <p> tag description
    var title = document.createElement("h2");
    title.innerHTML = titleText;

    var desc = document.createElement("p");
    desc.innerHTML = descText;
    
    // Adds the class 'server_title' both to the h2 tag and p tag
    title.className = "server_title";
    desc.className = "server_desc";

    // If full_desc is not null or undefined, set it as the tooltip of the description
    if (full_desc) {
        desc.title = full_desc;
    }

    // Append the title and description to the server
    server.appendChild(svg);
    server.appendChild(title);
    server.appendChild(desc);

    if (resource_usage != null) {
        // Handles adding resources
        var resources = document.createElement("div");
        resources.className = "resources";
        var ram_used = document.createElement("p");
        ram_used.className = "server_ram_used";
        ram_used.innerHTML = resource_usage['RAM']['used'] + " MB";

        var ram_total = document.createElement("p");
        ram_total.className = "server_ram_total";
        ram_total.innerHTML = resource_usage['RAM']['total'] + " MB";

        var cpu_used = document.createElement("p");
        cpu_used.className = "server_cpu_used";
        cpu_used.innerHTML = resource_usage['CPU']['used'] + "%";

        var cpu_allowed = document.createElement("p");
        cpu_allowed.className = "server_cpu_allowed";
        cpu_allowed.innerHTML = resource_usage['CPU']['allowed'] + "%";

        var disk_used_measurement = document.createElement("p");
        disk_used_measurement.className = "server_disk_used";
        disk_used_measurement.innerHTML = resource_usage['STORAGE']['used'] + " MB";

        var disk_total_measurement = document.createElement("p");
        disk_total_measurement.className = "server_disk_total";
        disk_total_measurement.innerHTML = resource_usage['STORAGE']['total'] + " MB";

        resources.appendChild(ram_used);
        resources.appendChild(ram_total);
        resources.appendChild(cpu_used);
        resources.appendChild(cpu_allowed);
        resources.appendChild(disk_used_measurement);
        resources.appendChild(disk_total_measurement);

        // Append the resources to the server
        server.appendChild(resources);
    }

    // Append the server to the server list container
    sl_container.appendChild(server);
}

function clearServers () {
    // Clear the server list container
    sl_container.innerHTML = "";
}

let old_servers = null

function getServers() {
    // Fetch the servers from the server list
    const token = localStorage.getItem('token');
    // View all switch. If it's ticked, set own_servers_only to false. Otherwise, set it to true.
    const own_servers_only = view_all_btn.checked == false;
    fetch("http://127.0.0.1:5005/api/servers/list", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            token: token,
            'own_servers_only': own_servers_only
        })
    })
    .then(response => {
        if (!response.ok) {
            // If the response status is not ok, throw an error to handle it in the catch block
            return response.json().then(errData => {
                throw new Error(errData.message);
            });
        }
        return response.json();
    })
    .then(data => {
        // Access the nested "servers" object
        const servers = data.servers;

        // If the server list is empty, add a "No servers" message
        if (Object.keys(servers).length == 0) {
            // Adds a "No servers" message
            clearServers();
            addServer("No servers", "No servers found", null, false);
            return;
        }
        clearServers();

        for (let server in servers) {
            let description = servers[server]['description'];
            // If the description is empty, set it to "No description"
            if (description == "" || description == null || description == undefined) {
                description = "No description";
            }
            // If the description is too long, truncate it
            if (description.length > 50) {
                // As a style, add the full description to the tooltip later.
                var full_desc = description;
                description = description.substring(0, 50) + "...";
            }

            const is_online = servers[server]['online'];
            const resource_usage = servers[server]['resources']; // A dictionary. Contains CPU, RAM, and Disk usage

            // Add the server to the server list
            addServer(server, description, full_desc, is_online, resource_usage);
            full_desc = null;
        }
    })
    .catch(error => {
        // Handle the 401 error by adding a server with "Insufficient permissions"
        clearServers();
        addServer("Insufficient permissions", error.message, null, false);
        console.warn('Stopping interval list servers...')
        clearInterval(intervalid);
    });
}

// Add a click event listener to the view all button that triggers the getServers function when clicked
view_all_btn.addEventListener("click", getServers);

getServers();
let intervalid = setInterval(getServers, 15000);
