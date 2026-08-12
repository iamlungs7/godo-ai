console.log("🔐 GODO AI Authentication Guard Loaded");

const authenticated =
    localStorage.getItem("godo_ai_authenticated");

const user =
    localStorage.getItem("godo_ai_user");

if (authenticated !== "true" || !user) {

    window.location.href = "login.html";

}
