console.log("👤 GODO AI Session UI Loaded");

const userSession =
    document.getElementById("userSession");

const storedUser =
    localStorage.getItem("godo_ai_user");


if (userSession && storedUser) {

    try {

        const user =
            JSON.parse(storedUser);


        userSession.innerHTML = `
            <div class="session-user">
                <strong>
                    👋 Welcome, ${user.full_name || "GODO AI User"}
                </strong>

                <span>
                    🔐 Authenticated
                </span>
            </div>

            <button
                id="logoutButton"
                class="btn-secondary">
                Logout
            </button>
        `;


        const logoutButton =
            document.getElementById("logoutButton");


        if (logoutButton) {

            logoutButton.addEventListener(
                "click",
                function() {

                    localStorage.removeItem(
                        "godo_ai_session_token"
                    );

                    localStorage.removeItem(
                        "godo_ai_authenticated"
                    );

                    localStorage.removeItem(
                        "godo_ai_user"
                    );


                    window.location.href =
                        "login.html";

                }
            );

        }


    } catch (error) {

        console.error(
            "❌ Unable to load GODO AI user session:",
            error
        );

    }

}
