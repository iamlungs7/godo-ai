console.log("☰ GODO AI Command Menu Loaded");

const menuButton = document.getElementById("godoMenuButton");
const menu = document.getElementById("godoMenu");
const menuClose = document.getElementById("godoMenuClose");
const logoutButton = document.getElementById("godoLogout");
const menuUser = document.getElementById("godoMenuUser");

if (menuButton && menu) {

    menuButton.addEventListener("click", function() {
        menu.classList.add("open");
    });

}

if (menuClose && menu) {

    menuClose.addEventListener("click", function() {
        menu.classList.remove("open");
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

        window.location.href = "login.html";

    });

}
