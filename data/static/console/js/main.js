/* Network Monitor - Main JS */

// Auto-dismiss toasts after 5 seconds
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toast.show").forEach(function (toast) {
        setTimeout(function () {
            var bsToast = bootstrap.Toast.getOrCreateInstance(toast);
            bsToast.hide();
        }, 5000);
    });
});
