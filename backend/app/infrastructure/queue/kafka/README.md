## infrastructure/queue/kafka

Kafka implementation cho message queue.

### Files

`publisher.py` - serialize domain event thành JSON, publish vào Kafka topic tương ứng.

`consumer.py` - base consumer wrapper: kết nối Kafka, listen topic, deserialize message, gọi handler function. Được subclass bởi từng consumer trong `consumers/`.
