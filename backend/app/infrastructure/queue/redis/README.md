## infrastructure/queue/redis

Redis Streams implementation cho message queue. Dùng cho local dev và môi trường nhỏ không cần Kafka.

### Files

`publisher.py` - publish domain event vào Redis Stream tương ứng dùng XADD.

`consumer.py` - base consumer wrapper: XREADGROUP để consume, ack sau khi xử lý xong. Subclassed bởi từng consumer trong `consumers/`.
