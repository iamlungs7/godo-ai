console.log("🔐 GODO AI Login Gateway Loaded");

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");

if (loginForm) {

    loginForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const email =
            document.getElementById("email").value.trim();

        const password =
            document.getElementById("password").value;


        if (!email || !password) {

            loginMessage.innerText =
                "Please enter your email and password.";

            return;
        }


        loginMessage.innerText =
            "🔐 Authenticating with GODO AI...";


        try {

            const response = await fetch(
                "https://godo-ai-production.up.railway.app/api/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );


            const data = await response.json();


            if (!response.ok) {

                loginMessage.innerText =
                    data.error || "Login failed.";

                return;
            }


            localStorage.setItem(
                "godo_ai_user",
                JSON.stringify(data.user)
            );


            localStorage.setItem(
                "godo_ai_session_token",
                data.session_token
            );


            localStorage.setItem(
                "godo_ai_authenticated",
                "true"
            );


            loginMessage.innerText =
                "✅ Login successful. Opening GODO AI...";


            setTimeout(() => {

                window.location.href =
                    "dashboard.html";

            }, 1000);


        } catch (error) {

            console.error(
                "Login error:",
                error
            );

            loginMessage.innerText =
                "Unable to connect to GODO AI authentication server.";

        }

    });

}

console.log("🔥 GODO AI LOGIN VERSION 2 ACTIVE");
