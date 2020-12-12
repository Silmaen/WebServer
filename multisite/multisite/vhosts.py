"""Creation d’un middleware pour la gestion des hôtes virtuels"""
virtual_hosts = {
    "www.argawaen.net": "www.urls_base",
    "drone.argawaen.net": "drone.urls_base",
    "testsubject.argawaen.net": "tsjt.urls_base",
    "ayoaron.argawaen.net": "ayoaron.urls_base",
    "127.0.0.1": "www.urls_base"
}


class VHostMiddleware:
    """Classe de gestion des hôtes virtuels"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # On cherche à connaitre quel seront les urls racines.
        host = request.get_host()
        if "127.0.0.1" in host:
            request.urlconf = virtual_hosts.get("127.0.0.1")
        else:
            request.urlconf = virtual_hosts.get(host)
        # Attention à l’ordre.
        response = self.get_response(request)
        return response
