console.log("🚀 GODO AI Dashboard v2 Started");

const REFRESH_INTERVAL = 5000;

const DATA = {
    signals: "assets/data/signal_statistics.json",
    prices: "assets/data/latest_prices.json",
    activeSignals: "assets/data/active_signals.json",
    activeTrades: "assets/data/active_trades.json",
    engine: "assets/data/engine_status.json",
    trades: "assets/data/trade_statistics.json"
};

async function fetchJSON(file) {
    const response = await fetch(file + "?t=" + Date.now());

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${file}`);
    }

    return response.json();
}

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.innerText = value;
    }
}

// ==========================
// GODO AI Account Profile
// ==========================

function loadAccountProfile() {

    const storedUser =
        localStorage.getItem("godo_ai_user");

    if (!storedUser) {

        setText("accountFullName", "Unknown");
        setText("accountId", "--");
        setText("accountEmail", "--");
        setText("accountStatus", "Not Authenticated");

        return;
    }

    try {

        const user =
            JSON.parse(storedUser);

        setText(
            "accountFullName",
            user.full_name || "GODO AI User"
        );

        setText(
            "accountId",
            user.id !== undefined
                ? "GODO-" + String(user.id).padStart(6, "0")
                : "--"
        );

        setText(
            "accountEmail",
            user.email || "--"
        );

        setText(
            "accountStatus",
            "Authenticated"
        );

    } catch (error) {

        console.error(
            "❌ Account profile error:",
            error
        );

        setText("accountFullName", "Unknown");
        setText("accountId", "--");
        setText("accountEmail", "--");
        setText("accountStatus", "Session Error");

    }
}

// ==========================
// Signal Statistics
// ==========================

async function loadSignalStatistics() {

    try {

        const data = await fetchJSON(DATA.signals);

        const wins = Number(data.wins || 0);
        const losses = Number(data.losses || 0);
        const breakeven = Number(data.breakeven || 0);
        const total = Number(data.total_signals || 0);

        setText("totalSignals", `Signals : ${total}`);
        setText("wins", `Wins : ${wins}`);
        setText("losses", `Losses : ${losses}`);
        setText("breakeven", `Breakeven : ${breakeven}`);

        const rate =
            total > 0
                ? ((wins / (wins + losses + breakeven)) * 100).toFixed(2)
                : "0.00";

        setText("summaryRate", `Win Rate : ${rate}%`);

    } catch (error) {

        console.error("Signal statistics error:", error);

        setText("totalSignals", "Signals : Error");
        setText("wins", "Wins : --");
        setText("losses", "Losses : --");
        setText("breakeven", "Breakeven : --");
    }
}

// ==========================
// Live Prices
// ==========================

async function loadPrices() {

    const box = document.getElementById("livePrices");

    if (!box) return;

    try {

        const data = await fetchJSON(DATA.prices);

        const prices = data.prices || {};

        const symbols = [
            "BTCUSD",
            "ETHUSD",
            "BNBUSD",
            "XAUUSD",
            "USDJPY",
            "EURUSD",
            "GBPUSD",
            "USDCAD",
            "AUDCAD",
            "NDX"


        ];

        let html = "";

        symbols.forEach(symbol => {

            if (prices[symbol] === undefined) return;

            const price = Number(prices[symbol]);

            html += `
                <div class="price-row">
                    <span>${symbol}</span>
                    <strong>${price.toFixed(5)}</strong>
                </div>
            `;
        });

        box.innerHTML = html || "Waiting for prices...";

        setText(
            "lastRefresh",
            "Last Refresh: " + new Date().toLocaleTimeString()
        );

    } catch (error) {

        console.error("Price error:", error);

        box.innerHTML = "Unable to load prices.";
    }
}

// ==========================
// Active Signals
// ==========================

async function loadActiveSignals() {

    const box = document.getElementById("activeSignals");

    if (!box) return;

    try {

        const data = await fetchJSON(DATA.activeSignals);

        const signals = Object.values(data || {});

        const count = document.getElementById("activeSignalsCount");

        if (count) {
            count.innerText = `${signals.length} Active Signal${signals.length === 1 ? "" : "s"}`;
        }

        if (signals.length === 0) {

            box.innerHTML = "No Active Signals";
            return;
        }

        let html = "";

        signals.forEach(signal => {

            const status =
                signal.status || "UNKNOWN";

            const protection =
                signal.protected
                    ? "🛡️ PROTECTED"
                    : "Unprotected";

            const statusClass =
                status.toLowerCase();

            html += `
                <div class="active-signal-card">

                    <div class="active-signal-header">

                        <strong>
                            #${signal.id} ${signal.symbol}
                        </strong>

                        <span class="status ${statusClass}">
                            ${status}
                        </span>

                    </div>

                    <div class="trade-direction">
                        ${signal.side}
                    </div>

                    <div class="trade-grid">

                        <div>
                            <span>Entry</span>
                            <strong>
                                ${Number(signal.entry_low).toFixed(5)}
                                -
                                ${Number(signal.entry_high).toFixed(5)}
                            </strong>
                        </div>

                        <div>
                            <span>Stop Loss</span>
                            <strong>
                                ${Number(signal.sl).toFixed(5)}
                            </strong>
                        </div>

                        <div>
                            <span>Take Profit</span>
                            <strong>
                                ${Number(signal.tp).toFixed(5)}
                            </strong>
                        </div>

                        <div>
                            <span>Protection</span>
                            <strong>
                                ${protection}
                            </strong>
                        </div>

                    </div>

                    <small>${signal.time || "--"}</small>

                </div>
            `;
        });

        box.innerHTML = html;

        setText(
            "summaryActive",
            `Active Signals : ${signals.length}`
        );

    } catch (error) {

        console.error("Active signals error:", error);

        box.innerHTML = "Unable to load active signals.";
    }
}

// ==========================
// Trade Statistics
// ==========================

async function loadTradingSummary() {

    try {

        const data = await fetchJSON(DATA.trades);

        const wins = Number(data.wins || 0);
        const losses = Number(data.losses || 0);
        const breakeven = Number(data.breakeven || 0);
        const active = Number(data.active_trades || 0);

        const totalClosed =
            wins + losses + breakeven;

        const rate =
            totalClosed > 0
                ? ((wins / totalClosed) * 100).toFixed(1)
                : "0.0";

        setText(
            "summaryActive",
            `Active Trades : ${active}`
        );

        setText(
            "summaryWins",
            `Wins : ${wins}`
        );

        setText(
            "summaryLosses",
            `Losses : ${losses}`
        );

        setText(
            "summaryBreakeven",
            `Breakeven : ${breakeven}`
        );

        setText(
            "summaryRate",
            `Win Rate : ${rate}%`
        );

    } catch (error) {

        console.error("Trade statistics error:", error);

        setText("summaryActive", "Active Signals : --");
        setText("summaryWins", "Wins : --");
        setText("summaryLosses", "Losses : --");
        setText("summaryBreakeven", "Breakeven : --");
        setText("summaryRate", "Win Rate : --");
    }
}

// ==========================
// Engine Status
// ==========================

async function loadEngineStatus() {

    try {

        const data = await fetchJSON(DATA.engine);

        setText(
            "engineStatus",
            data.status || "UNKNOWN"
        );

        setText(
            "scannerStatus",
            data.scanner || "UNKNOWN"
        );

        updateCountdown(
            data.last_scan,
            Number(data.next_scan || 300)
        );

    } catch (error) {

        console.error("Engine status error:", error);

        setText("engineStatus", "OFFLINE");
        setText("scannerStatus", "DATA ERROR");
    }
}

// ==========================
// Next Scan Countdown
// ==========================

function updateCountdown(lastScan, interval) {

    const element =
        document.getElementById("nextScan");

    if (!element) return;

    if (!lastScan) {

        element.innerText =
            formatSeconds(interval);

        return;
    }

    const scanTime =
        new Date(lastScan.replace(" ", "T"));

    const elapsed =
        Math.floor((Date.now() - scanTime.getTime()) / 1000);

    let remaining =
        interval - elapsed;

    if (remaining < 0) {
        remaining = 0;
    }

    element.innerText =
        formatSeconds(remaining);
}

function formatSeconds(seconds) {

    const min =
        Math.floor(seconds / 60);

    const sec =
        seconds % 60;

    return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

// ==========================
// Refresh Countdown
// ==========================

setInterval(() => {

    loadEngineStatus();

}, 1000);

// ==========================
// Dashboard Refresh
// ==========================

async function refreshDashboard() {

    loadAccountProfile();

    await Promise.all([
        loadSignalStatistics(),
        loadPrices(),
        loadActiveSignals(),
        loadActiveTrades(),
        loadTradingSummary(),
        loadEngineStatus()
    ]);

    console.log(
        "🔄 Dashboard refreshed:",
        new Date().toLocaleTimeString()
    );
}

// Initial load
refreshDashboard();

// Refresh every 5 seconds
setInterval(
    refreshDashboard,
    REFRESH_INTERVAL
);

// ==========================
// Active Signals Toggle
// ==========================

function toggleActiveSignals() {

    const box = document.getElementById("activeSignals");
    const arrow = document.getElementById("activeSignalsArrow");

    if (!box) return;

    box.classList.toggle("open");

    if (box.classList.contains("open")) {
        arrow.innerText = "▾";
    } else {
        arrow.innerText = "▸";
    }
}

