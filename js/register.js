console.log("📝 GODO AI Registration Gateway Loaded");

const registerForm = document.getElementById("registerForm");
const registerMessage = document.getElementById("registerMessage");

if (registerForm) {

    registerForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const name =
            document.getElementById("name").value.trim();

        const email =
            document.getElementById("email").value.trim();

        const password =
            document.getElementById("password").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;


        if (password !== confirmPassword) {

            registerMessage.innerText =
                "Passwords do not match.";

            return;
        }


        if (password.length < 8) {

            registerMessage.innerText =
                "Password must be at least 8 characters.";

            return;
        }


        registerMessage.innerText =
            "Creating your GODO AI account...";


        try {

            const response = await fetch(
                "https://godo-ai-production.up.railway.app/api/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        full_name: name,
                        email: email,
                        password: password
                    })
                }
            );


            const data = await response.json();


            if (!response.ok) {

                registerMessage.innerText =
                    data.error || "Registration failed.";

                return;
            }


            registerMessage.innerText =
                "✅ Account created successfully. Redirecting to login...";


            setTimeout(() => {

                window.location.href = "login.html";

            }, 1500);


        } catch (error) {

            console.error(
                "Registration error:",
                error
            );

            registerMessage.innerText =
                "Unable to connect to GODO AI authentication server.";

        }

    });

}
