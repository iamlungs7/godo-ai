console.log("🔐 GODO AI Password Reset Loaded");

const API_BASE =
    "https://godo-ai-production.up.railway.app";

const form =
    document.getElementById("forgotPasswordForm");

const emailInput =
    document.getElementById("forgotEmail");

const message =
    document.getElementById("forgotMessage");


form.addEventListener("submit", async function(event) {

    event.preventDefault();

    const email =
        emailInput.value.trim();

    if (!email) {
        message.innerText =
            "Please enter your email address.";
        return;
    }

    message.innerText =
        "⏳ Processing...";

    try {

        const response =
            await fetch(
                API_BASE + "/api/forgot-password",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email: email
                    })
                }
            );

        const data =
            await response.json();

        message.innerText =
            data.message ||
            "If the account exists, password reset instructions have been provided.";

    } catch (error) {

        console.error(
            "Password reset error:",
            error
        );

        message.innerText =
            "Unable to connect to GODO AI.";
    }

});
