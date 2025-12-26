# services_cache.py
from django.core.cache import cache
from .models import Service

SERVICE_CACHE_KEY = "service_tuples_v1"

def get_service_tuples():
    services = cache.get(SERVICE_CACHE_KEY)
    if services is None:
        services = tuple(
            Service.objects
            .filter(is_active=True)
            .values_list('code', 'name')
        )
        cache.set(SERVICE_CACHE_KEY, services, 86400)
    return services
