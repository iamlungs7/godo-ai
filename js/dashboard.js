alert("GODO AI Dashboard JS Loaded");
// ==========================
// GODO AI Dashboard Engine
// ==========================

console.log("🚀 GODO AI Dashboard Started");

// Platform Status
const platformStatus = "ONLINE";

// Development Mode
const environment = "Development";

// Last Update
const lastUpdate = new Date().toLocaleString();

// Console Output
console.log("Status :", platformStatus);
console.log("Environment :", environment);
console.log("Updated :", lastUpdate);

// ==========================
// Read Statistics JSON
// ==========================

fetch("assets/data/signal_statistics.json")
.then(response => response.json())
.then(data => {

document.getElementById("totalSignals").innerText =
"Signals : " + data.total_signals;

document.getElementById("wins").innerText =
"Wins : " + data.wins;

document.getElementById("losses").innerText =
"Losses : " + data.losses;

document.getElementById("breakeven").innerText =
"Breakeven : " + data.breakeven;

})
.catch(error => {

console.log(error);

});

//============================
//Latest Signals JSON
//============================

fetch("assets/data/latest_signals.json")
.then(response => response.json())
.then(data => {

    const box = document.getElementById("latestSignals");

    if (!data.signals || Object.keys(data.signals).length === 0) {
        box.innerHTML = "No signals available";
        return;
    }

    let html = "";

    for (const symbol in data.signals) {

        const lines = data.signals[symbol]
            .split("\n")
            .map(line => line.trim())
            .filter(line => line !== "");

        const direction = lines[3];
        const time = lines[lines.length - 1];

        html += `
            <div class="signal-card">
                <strong>${symbol}</strong><br>
                ${direction}<br>
                <small>${time}</small>
            </div>
            <hr>
        `;
    }

    box.innerHTML = html;

})
.catch(error => {
    console.log(error);
});
