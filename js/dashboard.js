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

function loadLatestSignals() {

    fetch("assets/data/latest_signals.json")
    .then(response => response.json())
    .then(data => {

        const box = document.getElementById("latestSignals");

        let html = "";

        for (const symbol in data.signals) {

            const signal = data.signals[symbol];

            const lines = signal.split("\n").filter(Boolean);

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

        if(html===""){
            html="Waiting for signals...";
        }

        box.innerHTML = html;

    });

.catch(error => {
        console.log(error);
    });

}

// ==========================
// Live Prices
// ==========================

function loadPrices(){

fetch("assets/data/latest_prices.json")
.then(response=>response.json())
.then(data=>{

const prices=data.prices;

document.getElementById("livePrices").innerHTML=`
<b>BTCUSD</b> : ${Number(prices.BTCUSD).toFixed(2)}<br>
<b>ETHUSD</b> : ${Number(prices.ETHUSD).toFixed(2)}<br>
<b>BNBUSD</b> : ${Number(prices.BNBUSD).toFixed(2)}<br>
<b>XAUUSD</b> : ${Number(prices.XAUUSD).toFixed(2)}<br>
<b>NDX</b> : ${Number(prices.NDX).toFixed(2)}
`;

});

.catch(error => console.log(error));

}

// ==========================
// Next Scan Countdown
// ==========================

let seconds = 300;

setInterval(() => {

    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;

    document.getElementById("nextScan").innerText =
    `${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;

    if (seconds > 0) {
        seconds--;
    } else {
        seconds = 300;
    }

}, 1000);

// ==========================
// Scanner Animation
// ==========================

const markets = [
    "BTCUSD",
    "ETHUSD",
    "BNBUSD",
    "XAUUSD",
    "NDX"
];

let i = 0;

setInterval(() => {

    document.getElementById("scannerStatus").innerText =
    "Scanning " + markets[i] + "...";

    i++;

    if (i >= markets.length) {
        i = 0;
    }

}, 1000);

// ==========================
// Auto Refresh Dashboard
// ==========================

loadLatestSignals();

loadPrices();

setInterval(()=>{

loadLatestSignals();

loadPrices();

},5000);
