/* Page de supervision : graphe d'état des appareils et liste des transitions.
 *
 * Sorti du gabarit, où il faisait 420 lignes en ligne. Les couleurs sont lues sur le
 * thème du site plutôt que réécrites ici, pour suivre `default_www.css`.
 */
(function () {
    "use strict";

    const script = document.getElementById("monitoring-dashboard-script");
    const timeseriesUrl = script.dataset.timeseriesUrl;

    // `categories` est sérialisé en liste de paires [valeur, libellé] par json_script.
    const categoryLabels = {};
    JSON.parse(document.getElementById("category-labels").textContent)
        .forEach(function (pair) { categoryLabels[pair[0]] = pair[1]; });

    let currentPeriod = "6h";
    let refreshTimer = null;
    let chart = null;
    let isolatedDeviceId = null;

    const periodBtns = document.querySelectorAll("#period-selector button");
    const refreshSelect = document.getElementById("refresh-interval");
    const refreshDot = document.getElementById("refresh-dot");
    const lastUpdateEl = document.getElementById("last-update");
    const chartInfo = document.getElementById("chart-info");
    const deviceSearch = document.getElementById("device-search");
    const deviceDropdownBtn = document.getElementById("device-dropdown-btn");
    const categoryDropdownBtn = document.getElementById("category-dropdown-btn");
    const changesBody = document.getElementById("state-changes-body");
    const changesCount = document.getElementById("changes-count");

    /* Une couleur du thème, par son nom de variable CSS. */
    function themeColor(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    const COLORS = {
        up: themeColor("--green"),
        failing: themeColor("--yellow"),
        down: themeColor("--red"),
        text: themeColor("--text"),
        muted: themeColor("--text-secondary"),
        surface: themeColor("--bg-surface"),
        border: themeColor("--border"),
    };

    // --- Filtres ------------------------------------------------------------

    function selectedCategories() {
        return Array.from(document.querySelectorAll(".category-checkbox:checked"))
            .map(function (cb) { return cb.value; });
    }

    function updateCategoryLabel() {
        const checked = document.querySelectorAll(".category-checkbox:checked").length;
        const total = document.querySelectorAll(".category-checkbox").length;
        categoryDropdownBtn.textContent = (checked === 0 || checked === total)
            ? "Toutes (" + total + ")"
            : checked + " / " + total;
    }

    function updateDeviceCount() {
        const checked = document.querySelectorAll(".device-checkbox:checked").length;
        const total = document.querySelectorAll(".device-checkbox").length;
        deviceDropdownBtn.textContent = (checked === total)
            ? "Tous (" + total + ")"
            : checked + " / " + total;
    }

    /* Restreint la liste d'appareils aux catégories cochées, puis recharge. */
    function onCategoryChange() {
        updateCategoryLabel();
        const selected = selectedCategories();
        document.querySelectorAll("#device-list .form-check").forEach(function (el) {
            const visible = selected.length === 0 || selected.includes(el.dataset.category);
            el.classList.toggle("is-hidden", !visible);
            el.querySelector("input").checked = visible;
        });
        updateDeviceCount();
        fetchData();
    }

    /* Bascule : n'afficher qu'un appareil, ou tout réafficher. */
    function isolateDevice(deviceId) {
        const isolate = isolatedDeviceId !== deviceId;
        document.querySelectorAll(".device-checkbox").forEach(function (cb) {
            cb.checked = isolate ? cb.value === deviceId : true;
        });
        isolatedDeviceId = isolate ? deviceId : null;
        updateDeviceCount();
        highlightStateChangeRows(isolatedDeviceId);
        fetchData();
    }

    function highlightStateChangeRows(deviceId) {
        document.querySelectorAll(".state-change-row").forEach(function (row) {
            row.classList.toggle("isolated", deviceId && row.dataset.deviceId === deviceId);
        });
    }

    /* (Re)programme le rafraîchissement automatique ; 0 = manuel. */
    function setupRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        const secs = parseInt(refreshSelect.value, 10);
        if (secs > 0) {
            refreshTimer = setInterval(fetchData, secs * 1000);
        }
        refreshDot.className = secs > 0 ? "refresh-indicator active" : "refresh-indicator paused";
    }

    /* Les filtres ne sont transmis que s'ils réduisent réellement la sélection. */
    function buildParams() {
        const params = new URLSearchParams({ period: currentPeriod });

        const categories = selectedCategories();
        const totalCategories = document.querySelectorAll(".category-checkbox").length;
        if (categories.length > 0 && categories.length < totalCategories) {
            params.set("categories", categories.join(","));
        }

        const devices = Array.from(document.querySelectorAll(".device-checkbox:checked"))
            .map(function (cb) { return cb.value; });
        const totalDevices = document.querySelectorAll(".device-checkbox").length;
        if (devices.length > 0 && devices.length < totalDevices) {
            params.set("devices", devices.join(","));
        }
        return params;
    }

    // --- Données ------------------------------------------------------------

    async function fetchData() {
        try {
            const response = await fetch(timeseriesUrl + "?" + buildParams());
            const data = await response.json();
            updateChart(data);
            updateStateChanges(data.state_changes || []);
            if (data.stats) {
                document.getElementById("stat-total").textContent = data.stats.total;
                document.getElementById("stat-up").textContent = data.stats.up;
                document.getElementById("stat-down").textContent = data.stats.down;
                document.getElementById("stat-failing").textContent = data.stats.failing;
            }
            lastUpdateEl.textContent = new Date().toLocaleTimeString("fr-FR");
            chartInfo.textContent = data.total_devices + " appareils, " + data.buckets.length + " points";
        } catch (error) {
            lastUpdateEl.textContent = "Erreur";
        }
    }

    function statusBadge(status) {
        if (status === "up") {
            return '<span class="badge text-bg-success">En ligne</span>';
        }
        if (status === "failing") {
            return '<span class="badge text-bg-warning">En erreur</span>';
        }
        return '<span class="badge text-bg-danger">Hors ligne</span>';
    }

    function updateStateChanges(changes) {
        changesCount.textContent = changes.length + " appareil" + (changes.length > 1 ? "s" : "");

        if (changes.length === 0) {
            changesBody.innerHTML =
                '<tr><td colspan="7" class="console-empty">Aucun changement d’état sur cette période</td></tr>';
            return;
        }

        changesBody.innerHTML = changes.map(function (device) {
            const last = device.changes[device.changes.length - 1];
            const transitions = device.changes.map(function (change) {
                return statusBadge(change.from)
                    + ' <i class="mdi mdi-arrow-right"></i> '
                    + statusBadge(change.to);
            }).join(" ");

            return '<tr class="state-change-row' + (isolatedDeviceId === device.id ? " isolated" : "")
                + '" data-device-id="' + device.id + '">'
                + "<td><strong>" + device.hostname + "</strong></td>"
                // col-secondaire : masquée sous 768 px, comme le <th> correspondant.
                + '<td class="col-secondaire"><code>' + device.ip + "</code></td>"
                + '<td class="col-secondaire"><span class="badge">' + (categoryLabels[device.category] || device.category) + "</span></td>"
                + "<td>" + statusBadge(device.current) + "</td>"
                + '<td class="col-secondaire">' + transitions + "</td>"
                + '<td class="col-secondaire"><small>' + new Date(last.time).toLocaleString("fr-FR") + "</small></td>"
                + '<td><button type="button" class="btn btn-sm isolate-btn" '
                + 'title="Afficher uniquement cet appareil"><i class="mdi mdi-eye"></i></button></td>'
                + "</tr>";
        }).join("");
    }

    // --- Graphe -------------------------------------------------------------

    /* Un dégradé vertical à partir d'une couleur du thème. */
    function gradient(ctx, color) {
        const grad = ctx.createLinearGradient(0, 0, 0, 400);
        grad.addColorStop(0, color + "66");
        grad.addColorStop(1, color + "05");
        return grad;
    }

    function dataset(label, values, color, ctx) {
        return {
            label: label,
            data: values,
            borderColor: color,
            backgroundColor: gradient(ctx, color),
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            pointHitRadius: 10,
            borderWidth: 2,
        };
    }

    /* Met à jour le graphe existant si possible, sinon le construit. */
    function updateChart(data) {
        const labels = data.buckets.map(function (b) { return new Date(b.t); });
        const up = data.buckets.map(function (b) { return b.up; });
        const failing = data.buckets.map(function (b) { return b.failing || 0; });
        const down = data.buckets.map(function (b) { return b.down; });
        const max = Math.max(data.total_devices, Math.max(0, ...up, ...failing, ...down) + 1);

        if (chart) {
            chart.data.labels = labels;
            chart.data.datasets[0].data = up;
            chart.data.datasets[1].data = failing;
            chart.data.datasets[2].data = down;
            chart.options.scales.y.max = max;
            chart.update("none");
            return;
        }

        const ctx = document.getElementById("upChart").getContext("2d");
        const grid = { color: COLORS.border };
        const ticks = { color: COLORS.muted };

        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    dataset("En ligne", up, COLORS.up, ctx),
                    dataset("En erreur", failing, COLORS.failing, ctx),
                    dataset("Hors ligne", down, COLORS.down, ctx),
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: COLORS.text, usePointStyle: true, pointStyle: "rectRounded", padding: 15 },
                    },
                    tooltip: {
                        backgroundColor: COLORS.surface,
                        titleColor: COLORS.text,
                        bodyColor: COLORS.text,
                        borderColor: COLORS.border,
                        borderWidth: 1,
                        callbacks: {
                            title: function (items) {
                                return new Date(items[0].parsed.x).toLocaleString("fr-FR");
                            },
                            label: function (item) {
                                return " " + item.dataset.label + " : " + item.parsed.y + " appareil(s)";
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        type: "time",
                        time: {
                            tooltipFormat: "dd/MM/yyyy HH:mm",
                            displayFormats: { minute: "HH:mm", hour: "HH:mm", day: "dd/MM" },
                        },
                        grid: grid,
                        ticks: Object.assign({ maxTicksLimit: 12 }, ticks),
                    },
                    y: {
                        beginAtZero: true,
                        max: max,
                        grid: grid,
                        ticks: Object.assign({
                            stepSize: 1,
                            callback: function (v) { return Number.isInteger(v) ? v : ""; },
                        }, ticks),
                        title: { display: true, text: "Appareils", color: COLORS.muted },
                    },
                },
            },
        });
    }

    // --- Branchements -------------------------------------------------------

    periodBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            periodBtns.forEach(function (b) { b.classList.remove("active"); });
            btn.classList.add("active");
            currentPeriod = btn.dataset.period;
            fetchData();
        });
    });

    document.getElementById("category-list").addEventListener("change", onCategoryChange);
    document.getElementById("select-all-categories").addEventListener("click", function () {
        document.querySelectorAll(".category-checkbox").forEach(function (cb) { cb.checked = true; });
        onCategoryChange();
    });
    document.getElementById("select-none-categories").addEventListener("click", function () {
        document.querySelectorAll(".category-checkbox").forEach(function (cb) { cb.checked = false; });
        onCategoryChange();
    });

    document.getElementById("device-list").addEventListener("change", function () {
        isolatedDeviceId = null;
        updateDeviceCount();
        fetchData();
    });
    document.getElementById("select-all-devices").addEventListener("click", function () {
        document.querySelectorAll("#device-list .form-check:not(.is-hidden) .device-checkbox")
            .forEach(function (cb) { cb.checked = true; });
        isolatedDeviceId = null;
        updateDeviceCount();
        fetchData();
    });
    document.getElementById("select-none-devices").addEventListener("click", function () {
        document.querySelectorAll(".device-checkbox").forEach(function (cb) { cb.checked = false; });
        isolatedDeviceId = null;
        updateDeviceCount();
        fetchData();
    });

    deviceSearch.addEventListener("input", function () {
        const query = deviceSearch.value.toLowerCase();
        document.querySelectorAll("#device-list .form-check").forEach(function (el) {
            el.classList.toggle("is-filtered", query !== "" && !el.dataset.hostname.includes(query));
        });
    });

    document.getElementById("reset-filters").addEventListener("click", function () {
        document.querySelectorAll(".category-checkbox").forEach(function (cb) { cb.checked = true; });
        document.querySelectorAll("#device-list .form-check").forEach(function (el) {
            el.classList.remove("is-hidden", "is-filtered");
        });
        document.querySelectorAll(".device-checkbox").forEach(function (cb) { cb.checked = true; });
        deviceSearch.value = "";
        isolatedDeviceId = null;
        updateCategoryLabel();
        updateDeviceCount();
        highlightStateChangeRows(null);
        fetchData();
    });

    refreshSelect.addEventListener("change", setupRefresh);
    document.getElementById("refresh-now").addEventListener("click", fetchData);

    // Délégation : les lignes de transitions sont réécrites à chaque rafraîchissement.
    changesBody.addEventListener("click", function (event) {
        const row = event.target.closest(".state-change-row");
        if (row) {
            isolateDevice(row.dataset.deviceId);
        }
    });

    updateCategoryLabel();
    updateDeviceCount();
    fetchData();
    setupRefresh();
})();
