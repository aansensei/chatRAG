## infrastructure/queue/kafka

Kafka implementation for the message queue.

### Files

`publisher.py` - serializes a domain event to JSON and publishes it to the corresponding Kafka topic.

`consumer.py` - base consumer wrapper: connects to Kafka, listens on a topic, deserializes messages, and calls a handler function. Subclassed by each consumer in `consumers/`.
