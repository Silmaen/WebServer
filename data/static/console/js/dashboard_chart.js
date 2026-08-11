/* Tableau de bord : répartition des appareils par catégorie. */
(function () {
    "use strict";

    const canvas = document.getElementById("categoryChart");
    const data = JSON.parse(document.getElementById("category-data").textContent);
    if (!canvas || data.length === 0) {
        return;
    }

    // Palette catégorielle : dix teintes distinctes, ce que le thème du site ne fournit
    // pas. Seules les couleurs de texte sont lues sur le thème.
    const CATEGORY_COLORS = {
        server: "#3f9d5c", network: "#4a8fd4", ap: "#8a6fc4",
        iot: "#d98a3a", printer: "#8a8a8a", workstation: "#3fb9a0",
        phone: "#4ab9d4", camera: "#c4629b", other: "#a0a0a0", unknown: "#5a5a5a",
    };
    const FALLBACK = CATEGORY_COLORS.other;

    const textColor = getComputedStyle(document.documentElement)
        .getPropertyValue("--text").trim();

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: data.map(function (item) { return item.label; }),
            datasets: [{
                data: data.map(function (item) { return item.count; }),
                backgroundColor: data.map(function (item) {
                    return CATEGORY_COLORS[item.label] || FALLBACK;
                }),
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "right", labels: { color: textColor, padding: 10 } },
            },
        },
    });
})();
