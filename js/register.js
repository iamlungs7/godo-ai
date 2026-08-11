console.log("📝 GODO AI Registration Gateway Loaded");

const registerForm = document.getElementById("registerForm");
const registerMessage = document.getElementById("registerMessage");

if (registerForm) {

    registerForm.addEventListener("submit", function(event) {

        event.preventDefault();

        const password =
            document.getElementById("password").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        if (password !== confirmPassword) {

            registerMessage.innerText =
                "Passwords do not match.";

            return;
        }

        registerMessage.innerText =
            "Registration service is being prepared.";

    });

}
