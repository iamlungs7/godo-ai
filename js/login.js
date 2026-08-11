console.log("🔐 GODO AI Login Gateway Loaded");

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");

if (loginForm) {

    loginForm.addEventListener("submit", function(event) {

        event.preventDefault();

        loginMessage.innerText =
            "Authentication service is being prepared.";

    });

}
