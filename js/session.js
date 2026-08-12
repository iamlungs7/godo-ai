console.log("👤 GODO AI User Session Loaded");

const userSession = document.getElementById("userSession");

const authenticated =
    localStorage.getItem("godo_ai_authenticated");

const storedUser =
    localStorage.getItem("godo_ai_user");

if (authenticated === "true" && storedUser && userSession) {

    try {

        const user = JSON.parse(storedUser);

        userSession.innerHTML = `
            <div class="session-user">
                <strong>👋 Welcome, ${user.full_name || "GODO AI User"}</strong>
                <span>🔐 Authenticated</span>
            </div>

            <button id="logoutButton" class="btn-secondary">
                Logout
            </button>
        `;

        const logoutButton =
            document.getElementById("logoutButton");

        logoutButton.addEventListener("click", function() {

            localStorage.removeItem("godo_ai_authenticated");
            localStorage.removeItem("godo_ai_user");

            window.location.href = "login.html";

        });

    } catch (error) {

        console.error(
            "Session error:",
            error
        );

    }

}
