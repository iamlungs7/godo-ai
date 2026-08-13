console.log("🔐 GODO AI Server Authentication Guard Loaded");

const sessionToken =
    localStorage.getItem("godo_ai_session_token");


async function checkAuthentication() {

    if (!sessionToken) {

        console.warn("⚠️ No GODO AI session token.");

        localStorage.removeItem("godo_ai_authenticated");
        localStorage.removeItem("godo_ai_user");

        document.body.innerHTML = "<h2 style=\"color:red;padding:30px\">GODO DEBUG: NO SESSION TOKEN</h2>"; return;

        return;
    }


    try {

        const response = await fetch(
            "https://godo-ai-production.up.railway.app/api/session",
            {
                method: "GET",

                headers: {
                    "Authorization":
                        "Bearer " + sessionToken
                }
            }
        );


        const data = await response.json();


        if (!response.ok || !data.authenticated) {

            console.warn(
                "⚠️ GODO AI session rejected."
            );

            localStorage.removeItem(
                "godo_ai_session_token"
            );

            localStorage.removeItem(
                "godo_ai_authenticated"
            );

            localStorage.removeItem(
                "godo_ai_user"
            );

            document.body.innerHTML = "<h2 style=\"color:red;padding:30px\">GODO DEBUG: SERVER REJECTED SESSION</h2>"; return;

            return;
        }


        localStorage.setItem(
            "godo_ai_authenticated",
            "true"
        );


        localStorage.setItem(
            "godo_ai_user",
            JSON.stringify(data.user)
        );


        console.log(
            "✅ GODO AI server authorization successful"
        );

    } catch (error) {

        console.error(
            "❌ GODO AI authentication error:",
            error
        );

        window.location.href =
            "login.html";

    }

}


checkAuthentication();
