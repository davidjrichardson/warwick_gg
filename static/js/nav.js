document.addEventListener('DOMContentLoaded', function () {
    // Get all "navbar-burger" elements
    const navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);

    // Check if there are any navbar burgers
    if (navbarBurgers.length > 0) {
        // Add a click event on each of them
        navbarBurgers.forEach(function (el) {
            el.addEventListener('click', function () {
                // Get the target from the "data-target" attribute
                let target = el.dataset.target;
                let domTarget = document.getElementById(target);

                // Toggle the class on both the "navbar-burger" and the "navbar-menu"
                el.classList.toggle('is-active');
                domTarget.classList.toggle('is-active');
            });
        });
    }

    // POST logout request
    const logout = document.getElementById('logout');
    logout.addEventListener('click', function($ev) {
        $ev.preventDefault();
        $ev.stopImmediatePropagation();

        const csrf = Cookies.get('csrftoken');
        const http = new XMLHttpRequest();

        http.open('POST', '/accounts/logout/', true);
        http.setRequestHeader('X-CSRFToken', csrf);
        http.onreadystatechange = function () {
            if (http.readyState === 4 && http.status === 200) {
                window.location.replace('/');
            }

            console.log(http.statusText);
        };
        http.send('submit=true');

        return false;
    });
});