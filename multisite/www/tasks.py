"""Tâches Celery pour la vérification des machines et serveurs."""
import json
import logging
import socket
import subprocess
import urllib.request
import urllib.error

from celery import shared_task
from django.utils import timezone

from .models import Machine, Serveur

logger = logging.getLogger(__name__)

PORTS_COURANTS = "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,9090,27017"

TAILLE_CHUNK_PORTS = 50
NMAP_TIMEOUT_CHUNK = 60
NMAP_SUBPROCESS_TIMEOUT = 90


def _ping(ip):
    """Vérifie la connectivité via ping système (fonctionne sans root)."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", ip],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except Exception as e:
        logger.warning("Erreur ping %s : %s", ip, e)
        return False


def _sse_event(event, data):
    """Formate un événement SSE."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _resoudre_et_mettre_a_jour(machine):
    """Résout l'IP via DNS et met à jour la machine. Retourne (ip, alerte)."""
    ip, alerte = machine.resoudre_ip()
    machine.adresse_ip = ip
    machine.alerte_ip = alerte
    machine.save(update_fields=["adresse_ip", "alerte_ip"])
    return ip, alerte


def _expand_ports(port_string):
    """Expanse une chaîne de ports en liste d'entiers.

    Accepte des ports individuels et des plages : "22,80,9000-9100"
    → [22, 80, 9000, 9001, ..., 9100].
    """
    ports = []
    if not port_string:
        return ports
    for partie in port_string.split(","):
        partie = partie.strip()
        if not partie:
            continue
        if "-" in partie:
            debut, fin = partie.split("-", 1)
            try:
                ports.extend(range(int(debut), int(fin) + 1))
            except ValueError:
                continue
        else:
            try:
                ports.append(int(partie))
            except ValueError:
                continue
    return ports


@shared_task
def verifier_machines():
    """Vérifie l'état de toutes les machines réseau (résolution DNS + ping)."""
    maintenant = timezone.now()
    for machine in Machine.objects.all():
        ip, alerte = _resoudre_et_mettre_a_jour(machine)
        machine.en_ligne = _ping(ip) if ip else False
        machine.derniere_verification = maintenant
        if machine.en_ligne:
            machine.derniere_vue_en_ligne = maintenant
        machine.save()
        logger.info("Machine %s : %s", machine.nom, "en ligne" if machine.en_ligne else "hors ligne")


def scanner_ping(machine_id):
    """Générateur SSE : résout l'IP et vérifie la connectivité d'une machine."""
    machine = Machine.objects.get(pk=machine_id)
    maintenant = timezone.now()

    ip, alerte = _resoudre_et_mettre_a_jour(machine)
    en_ligne = _ping(ip) if ip else False
    machine.en_ligne = en_ligne
    machine.derniere_verification = maintenant
    if en_ligne:
        machine.derniere_vue_en_ligne = maintenant
    machine.save()
    yield _sse_event("ping", {
        "en_ligne": en_ligne,
        "adresse_ip": ip or "",
        "alerte_ip": alerte,
    })
    yield _sse_event("done", {"message": "Ping terminé"})


def scanner_ports(machine_id):
    """Générateur SSE : scanne les ports ouverts d'une machine par morceaux."""
    import nmap  # installé uniquement en Docker

    machine = Machine.objects.get(pk=machine_id)
    ip, _alerte = _resoudre_et_mettre_a_jour(machine)
    maintenant = timezone.now()

    if not ip:
        machine.ports_ouverts = []
        machine.dernier_scan_ports = maintenant
        machine.save()
        yield _sse_event("ports", {"ports_ouverts": []})
        yield _sse_event("done", {"message": "Scan des ports terminé"})
        return

    # Construire la liste complète de ports, dédupliquer et trier
    tous_ports = _expand_ports(PORTS_COURANTS)
    if machine.ports_supplementaires:
        tous_ports.extend(_expand_ports(machine.ports_supplementaires))
    tous_ports = sorted(set(tous_ports))

    # Découper en chunks
    chunks = [tous_ports[i:i + TAILLE_CHUNK_PORTS] for i in range(0, len(tous_ports), TAILLE_CHUNK_PORTS)]

    ports_ouverts_cumul = []
    erreurs = 0
    nm = nmap.PortScanner()

    for chunk in chunks:
        chunk_str = ",".join(str(p) for p in chunk)
        try:
            nm.scan(ip, chunk_str, arguments=f"-sV --host-timeout {NMAP_TIMEOUT_CHUNK}", timeout=NMAP_SUBPROCESS_TIMEOUT)
            if ip in nm.all_hosts():
                for proto in nm[ip].all_protocols():
                    for port in sorted(nm[ip][proto].keys()):
                        info = nm[ip][proto][port]
                        if info["state"] == "open":
                            ports_ouverts_cumul.append({
                                "port": port,
                                "protocole": proto,
                                "service": info.get("name", ""),
                                "version": info.get("version", ""),
                            })
        except Exception as e:
            erreurs += 1
            logger.warning("Erreur scan ports %s (chunk %s) : %s", ip, chunk_str, e)

        machine.ports_ouverts = ports_ouverts_cumul
        machine.dernier_scan_ports = maintenant
        machine.save(update_fields=["ports_ouverts", "dernier_scan_ports"])
        yield _sse_event("ports", {"ports_ouverts": ports_ouverts_cumul})

    message = "Scan des ports terminé"
    if erreurs:
        message = f"Scan terminé avec {erreurs} erreur(s) sur {len(chunks)} groupe(s)"
    yield _sse_event("done", {"message": message})


@shared_task
def verifier_serveurs():
    """Vérifie l'état de tous les serveurs."""
    maintenant = timezone.now()
    for serveur in Serveur.objects.all():
        _check_serveur(serveur, maintenant)
        serveur.save()
        logger.info("Serveur %s : %s", serveur.titre, "en ligne" if serveur.en_ligne else "hors ligne")


def _check_serveur(serveur, maintenant):
    """Vérifie l'état d'un serveur et met à jour ses champs (sans save)."""
    url_ok = False
    tcp_ok = False

    # Vérification HTTP via URL
    if serveur.url:
        url_ok = _verifier_url(serveur.url)

    # Vérification TCP directe
    hote = serveur.adresse_effective()
    if hote and serveur.port:
        tcp_ok = _verifier_tcp(hote, serveur.port)

    # Déterminer le statut en ligne
    if serveur.url and hote and serveur.port:
        serveur.en_ligne = url_ok or tcp_ok
        serveur.reverse_proxy_ok = url_ok and tcp_ok
    elif serveur.url:
        serveur.en_ligne = url_ok
        serveur.reverse_proxy_ok = False
    else:
        serveur.en_ligne = tcp_ok
        serveur.reverse_proxy_ok = False

    serveur.derniere_verification = maintenant
    if serveur.en_ligne:
        serveur.derniere_vue_en_ligne = maintenant


def scanner_serveur(serveur_id):
    """Générateur SSE : vérifie l'état d'un serveur."""
    serveur = Serveur.objects.get(pk=serveur_id)
    maintenant = timezone.now()
    _check_serveur(serveur, maintenant)
    serveur.save()

    data = {
        "en_ligne": serveur.en_ligne,
        "reverse_proxy_ok": serveur.reverse_proxy_ok,
    }
    yield _sse_event("check", data)
    yield _sse_event("done", {"message": "Vérification terminée"})


def _verifier_url(url):
    """Vérifie qu'une URL répond avec un code HTTP < 500."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "ArgawaenMonitoring/1.0")
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception as e:
        logger.debug("Erreur vérification URL %s : %s", url, e)
        return False


def _verifier_tcp(adresse, port):
    """Vérifie qu'un service TCP répond sur adresse:port."""
    try:
        with socket.create_connection((adresse, port), timeout=10):
            return True
    except Exception as e:
        logger.debug("Erreur vérification TCP %s:%s : %s", adresse, port, e)
        return False
