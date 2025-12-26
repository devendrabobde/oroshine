# middleware/rate_limit.py
import redis
from django.http import JsonResponse
from django.conf import settings

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

RATE_LIMIT_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
end
if count > tonumber(ARGV[1]) then return 0 end
return 1
"""

rate_limit_script = r.register_script(RATE_LIMIT_LUA)

class RedisIPRateLimitMiddleware:
    LIMIT = 10      # requests
    WINDOW = 60     # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        key = f"rl:{ip}"

        allowed = rate_limit_script(
            keys=[key],
            args=[self.LIMIT, self.WINDOW]
        )

        if allowed == 0:
            return JsonResponse(
                {"error": "Too many requests"},
                status=429
            )

        return self.get_response(request)
