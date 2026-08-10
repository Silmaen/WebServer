/* Console - le strict nécessaire.
 *
 * Auparavant ce fichier appelait `bootstrap.Toast` : la console chargeait tout le
 * bundle JS de Bootstrap depuis un CDN pour faire disparaître un message au bout de
 * cinq secondes. Le voici sans dépendance.
 */
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toast").forEach(function (toast) {
        setTimeout(function () {
            toast.style.transition = "opacity .4s";
            toast.style.opacity = "0";
            setTimeout(function () { toast.remove(); }, 400);
        }, 5000);
    });
});
