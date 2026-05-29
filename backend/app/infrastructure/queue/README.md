## infrastructure/queue

Message queue implementations. Kafka for production (high throughput, persistent), Redis Streams for local dev (simple, no Kafka cluster required).

Both implement the same interface from `domain/repositories/queue_repo.py`, so swapping only requires changing the DI binding.

### Subdirectories

`kafka/` - Kafka producer and consumer

`redis/` - Redis Streams producer and consumer
