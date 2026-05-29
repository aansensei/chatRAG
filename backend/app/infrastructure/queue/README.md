## infrastructure/queue

Message queue implementations. Kafka cho production (throughput cao, persistent), Redis Streams cho local dev (đơn giản, không cần Kafka cluster).

Cả hai implement cùng interface từ `domain/repositories/queue_repo.py`, nên swap chỉ cần đổi DI binding.

### Subdirectories

`kafka/` - Kafka producer/consumer

`redis/` - Redis Streams producer/consumer
