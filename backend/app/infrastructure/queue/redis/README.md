## infrastructure/queue/redis

Redis Streams implementation for the message queue. Used for local dev and small environments that don't need Kafka.

### Files

`publisher.py` - publishes a domain event to the corresponding Redis Stream using XADD.

`consumer.py` - base consumer wrapper: XREADGROUP to consume, ACK after successful processing. Subclassed by each consumer in `consumers/`.
