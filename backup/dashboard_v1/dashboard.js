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

        if (!data.signals || Object.keys(data.signals).length === 0) {
            box.innerHTML = "Waiting for signals...";
            return;
        }

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

        box.innerHTML = html;

    })

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
document.getElementById("lastRefresh").innerText =
"Last Refresh: " + new Date().toLocaleTimeString();

})

.catch(error => console.log(error));

}

// ==========================
// Active Trades
// ==========================

function loadActiveTrades() {

    fetch("assets/data/active_signals.json")
    .then(response => response.json())
    .then(data => {

        const box = document.getElementById("activeTrades");

        if (!data || data.length === 0) {
            box.innerHTML = "No Active Trades";
            return;
        }

        let html = "";

        data.forEach(trade => {

            let statusColor = "#ffffff";

            switch (trade.status) {

                case "ACTIVE":
                    statusColor = "#00ff66";
                    break;

                case "WIN":
                    statusColor = "#00bfff";
                    break;

                case "LOSS":
                    statusColor = "#ff4444";
                    break;

                case "BREAKEVEN":
                    statusColor = "#ffaa00";
                    break;

                case "PROTECTED":
                    statusColor = "#ffd700";
                    break;

            }

            html += `
            <div class="signal-card">

            <strong>${trade.symbol}</strong><br>

            ${trade.side}<br><br>

            Entry :
            ${Number(trade.entry_low).toFixed(2)}
            -
            ${Number(trade.entry_high).toFixed(2)}
            <br>

            TP :
            ${Number(trade.tp).toFixed(2)}
            <br>

            SL :
            ${Number(trade.sl).toFixed(2)}
            <br><br>

            Status :
            <b style="color:${statusColor}">
            ${trade.status}
            </b>
            </div>

            <hr>
            `;

        });

        box.innerHTML = html;

    })

    .catch(error => console.log(error));

}

// ==========================
// Engine Status
// ==========================

function loadEngineStatus(){

fetch("assets/data/engine_status.json")
.then(response => response.json())
.then(data => {

document.getElementById("engineStatus").innerText =
data.status;

document.getElementById("scannerStatus").innerText =
data.scanner;

})
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
// Auto Refresh Dashboard
// ==========================

loadLatestSignals();

loadPrices();

loadTradingSummary();

loadActiveTrades();

loadEngineStatus();

setInterval(()=>{

loadLatestSignals();

loadPrices();

loadTradingSummary();

loadActiveTrades();

loadEngineStatus();

},5000);

//===========================
// Trade Summary
//===========================

function loadTradingSummary(){

fetch("assets/data/trade_statistics.json")

.then(response=>response.json())

.then(data=>{

const wins=data.wins || 0;

const losses=data.losses || 0;

const breakeven=data.breakeven || 0;

const total=wins+losses+breakeven;

const active = data.active_trades || 0;

const rate=
total===0
?0
:((wins/total)*100).toFixed(1);

document.getElementById("summaryActive").innerText =
"Active Trades : " + active;

document.getElementById("summaryWins").innerText=
"Wins : "+wins;

document.getElementById("summaryLosses").innerText=
"Losses : "+losses;

document.getElementById("summaryBreakeven").innerText=
"Breakeven : "+breakeven;

document.getElementById("summaryRate").innerText=
"Win Rate : "+rate+"%";

});

}
