console.log("☰ GODO AI Command Menu Loaded");

const menuButton = document.getElementById("godoMenuButton");
const menu = document.getElementById("godoMenu");
const menuClose = document.getElementById("godoMenuClose");
const logoutButton = document.getElementById("godoLogout");
const menuUser = document.getElementById("godoMenuUser");


function closeMenu() {

    if (menu) {
        menu.classList.remove("open");
    }

}


function toggleMenu() {

    if (menu) {
        menu.classList.toggle("open");
    }

}


if (menuButton && menu) {

    menuButton.addEventListener("click", function(event) {

        event.stopPropagation();

        toggleMenu();

    });

}


if (menuClose && menu) {

    menuClose.addEventListener("click", function(event) {

        event.stopPropagation();

        closeMenu();

    });

}


if (menuUser) {

    const storedUser =
        localStorage.getItem("godo_ai_user");

    if (storedUser) {

        try {

            const user = JSON.parse(storedUser);

            menuUser.innerText =
                "👤 " + (user.full_name || "GODO AI User");

        } catch (error) {

            console.error(
                "Unable to load user session:",
                error
            );

        }

    }

}


if (logoutButton) {

    logoutButton.addEventListener("click", function() {

        localStorage.removeItem("godo_ai_authenticated");
        localStorage.removeItem("godo_ai_user");

        closeMenu();

        window.location.href = "login.html";

    });

}


document.addEventListener("click", function(event) {

    if (!menu || !menu.classList.contains("open")) {
        return;
    }

    if (
        !menu.contains(event.target) &&
        event.target !== menuButton
    ) {

        closeMenu();

    }

});
