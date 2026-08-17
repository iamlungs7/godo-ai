console.log("📝 GODO AI Registration Gateway Loaded");

const registerForm =
    document.getElementById("registerForm");

const registerMessage =
    document.getElementById("registerMessage");


if (registerForm) {

    registerForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const name =
                document.getElementById("name").value.trim();

            const email =
                document.getElementById("email").value.trim();

            const phone =
                document.getElementById("phone").value.trim();

            const country =
                document.getElementById("country").value.trim();

            const region =
                document.getElementById("region").value.trim();

            const city =
                document.getElementById("city").value.trim();

            const identityNumber =
                document.getElementById(
                    "identityNumber"
                ).value.trim();

            const password =
                document.getElementById("password").value;

            const confirmPassword =
                document.getElementById(
                    "confirmPassword"
                ).value;


            if (
                !name ||
                !email ||
                !phone ||
                !country ||
                !region ||
                !city ||
                !identityNumber ||
                !password ||
                !confirmPassword
            ) {

                registerMessage.innerText =
                    "Please complete all required fields.";

                return;
            }


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
                "🔐 Creating your secure GODO AI account...";


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
                            phone_number: phone,
                            country: country,
                            region: region,
                            city: city,
                            identity_number: identityNumber,
                            password: password
                        })
                    }
                );


                const data =
                    await response.json();


                if (!response.ok) {

                    registerMessage.innerText =
                        data.error ||
                        "Registration failed.";

                    return;
                }


                registerMessage.innerText =
                    "✅ Account created. Please verify your email and phone number.";


                setTimeout(() => {

                    window.location.href =
                        "login.html";

                }, 1800);


            } catch (error) {

                console.error(
                    "Registration error:",
                    error
                );

                registerMessage.innerText =
                    "Unable to connect to GODO AI authentication server.";

            }

        }
    );

}


console.log(
    "🔥 GODO AI REGISTRATION VERSION 3 ACTIVE"
);
