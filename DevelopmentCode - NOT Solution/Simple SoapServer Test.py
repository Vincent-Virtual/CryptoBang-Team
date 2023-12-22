import time
from confluent_kafka import Consumer, KafkaError

# Kafka configuration
kafka_config = {
    'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker(s)
    'group.id': 'my-consumer-group',
    'auto.offset.reset': 'earliest'
}

# Kafka topic to consume from
kafka_topic = 'your-kafka-topic'

# Create a Kafka consumer instance
consumer = Consumer(kafka_config)
consumer.subscribe([kafka_topic])

# Buffer for storing the last 10 seconds of data
data_buffer = []

# Function to process messages from Kafka
def process_message(message):
    data = message.value().decode('utf-8')
    data_buffer.append(data)

# Main loop to consume and return streaming data
while True:
    message = consumer.poll(1.0)  # Wait for Kafka messages for up to 1 second

    if message is not None and not message.error():
        process_message(message)

    # Remove data older than 10 seconds from the buffer
    current_time = time.time()
    data_buffer = [data for data in data_buffer if current_time - float(data.split(',')[0]) <= 10]

    # Return live streaming data (for demonstration purposes, we print it)
    print("Live Streaming Data:")
    for data in data_buffer:
        print(data)
    
    # Sleep for a while (adjust the sleep time as needed)
    time.sleep(2)  # Sleep for 2 seconds before checking for more data
