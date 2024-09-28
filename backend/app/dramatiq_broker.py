import dramatiq
from dramatiq.brokers.redis import RedisBroker
from config import cfg

redis_broker = RedisBroker(url=cfg.dramatiq.broker)
dramatiq.set_broker(redis_broker)
