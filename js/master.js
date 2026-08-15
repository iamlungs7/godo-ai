console.log("👑 GODO AI Master Control Loaded");


const API_BASE =
    "https://godo-ai-production.up.railway.app";


const sessionToken =
    localStorage.getItem("godo_ai_session_token");


function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.innerText = value;
    }
}


async function loadMasterOverview() {

    if (!sessionToken) {

        window.location.href =
            "login.html";

        return;
    }


    try {

        const response =
            await fetch(
                API_BASE +
                "/api/master/overview",
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            "Bearer " +
                            sessionToken
                    }
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (
                response.status === 401 ||
                response.status === 403
            ) {

                console.warn(
                    "Master authorization rejected"
                );

                window.location.href =
                    "dashboard.html";

                return;
            }


            throw new Error(
                data.error ||
                "Master API error"
            );
        }


        const master =
            data.master || {};

        const overview =
            data.overview || {};

        const users =
            data.users || [];


        setText(
            "masterName",
            master.full_name || "--"
        );

        setText(
            "masterId",
            "GODO-" +
            String(master.id || "").padStart(6, "0")
        );

        setText(
            "masterEmail",
            master.email || "--"
        );

        setText(
            "masterRole",
            master.role || "--"
        );


        setText(
            "totalUsers",
            overview.total_users || 0
        );

        setText(
            "activeSessions",
            overview.active_sessions || 0
        );

        setText(
            "securityStatus",
            "MASTER VERIFIED"
        );


        renderUsers(users);


        console.log(
            "✅ Master overview loaded"
        );

    } catch (error) {

        console.error(
            "❌ Master overview error:",
            error
        );

        setText(
            "securityStatus",
            "API ERROR"
        );

        const table =
            document.getElementById(
                "usersTable"
            );

        if (table) {

            table.innerHTML =
                "<p>Unable to load master data.</p>";
        }
    }
}


function renderUsers(users) {

    const table =
        document.getElementById(
            "usersTable"
        );

    if (!table) return;


    if (!users.length) {

        table.innerHTML =
            "<p>No registered accounts.</p>";

        return;
    }


    let html = `

        <div class="master-users">

            <div class="master-user-row master-user-header">

                <strong>ID</strong>
                <strong>Name</strong>
                <strong>Email</strong>
                <strong>Role</strong>
                <strong>Created</strong>

            </div>
    `;


    users.forEach(user => {

        const role =
            user.role || "user";


        html += `

            <div class="master-user-row">

                <span>
                    GODO-${String(user.id)
                        .padStart(6, "0")}
                </span>

                <span>
                    ${user.full_name || "--"}
                </span>

                <span>
                    ${user.email || "--"}
                </span>

                <span>
                    ${role.toUpperCase()}
                </span>

                <span>
                    ${user.created_at || "--"}
                </span>

            </div>

        `;
    });


    html += `
        </div>
    `;


    table.innerHTML = html;
}


const logout =
    document.getElementById(
        "masterLogout"
    );


if (logout) {

    logout.addEventListener(
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


loadMasterOverview();
