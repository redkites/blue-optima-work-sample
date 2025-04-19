import pika
import time
import json
import random
import argparse
import uuid
import threading

def generate_message():
    """Generates a message with a consistent input structure and a unique ID."""
    message_id = str(uuid.uuid4())
    input_data = [random.uniform(0, 1) for _ in range(5)]
    send_timestamp = time.time()
    return message_id, json.dumps({"message_id": message_id, "data": input_data, "send_timestamp": send_timestamp})

def receive_response(ch, method, properties, body, responses):
    """Callback function to handle responses from the queue."""
    # print(response['message_id'])
    response = json.loads(body.decode())
    message_id = response.get('message_id')
    print(f"Received response for message_id: {message_id}")  # Debugging log
    responses[message_id] = response
    ch.basic_ack(delivery_tag=method.delivery_tag)

def send_messages(host: str, queue_name: str, num_messages: int, response_queue_name: str, timeout: int):
    """Sends messages to the RabbitMQ queue and collects responses."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    responses = {}
    expected_responses = num_messages

    def start_consuming():
        response_connection = pika.BlockingConnection(pika.ConnectionParameters(host)) # Create a new connection for the thread
        response_channel = response_connection.channel()
        response_channel.queue_declare(queue=response_queue_name, durable=False)
        print(f"Consuming responses from queue: {response_queue_name}")  # Debugging log
        response_channel.basic_consume(
            queue=response_queue_name,
            on_message_callback=lambda ch, method, properties, body: receive_response(response_channel, method, properties, body, responses),
            auto_ack=False
        )
        try:
            response_channel.start_consuming()
        except KeyboardInterrupt:
            print("Stopping response consumer...")

    response_thread = threading.Thread(target=start_consuming)
    response_thread.daemon = True
    response_thread.start()

    sent_messages = {}
    start_time = time.time()
    for i in range(num_messages):
        message_id, message_body = generate_message()
        sent_messages[message_id] = json.loads(message_body)['send_timestamp']
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                reply_to=response_queue_name,
                correlation_id=message_id,
            ))
        if (i + 1) % 100 == 0:
            print(f"Sent {i + 1} messages...")

    end_time = time.time()
    total_send_time = end_time - start_time
    average_send_time = total_send_time / num_messages if num_messages > 0 else 0

    print(f"\nSent {num_messages} messages in {total_send_time:.2f} seconds.")
    print(f"Average send time: {average_send_time:.4f} seconds per message.")

    # Wait for all responses (with a timeout)
    print(f"Using the timeout of {timeout} seconds to wait for responses.")
    start_wait = time.time()
    while len(responses) < expected_responses and time.time() - start_wait < timeout:
        time.sleep(0.1)

    # Check if we received all expected responses
    if len(responses) < expected_responses:
        print(f"Timeout reached. Expected {expected_responses} responses, but received {len(responses)}.")

    connection.close()

    # Calculate metrics
    metrics = list()
    for msg_id, response in responses.items():
        if msg_id in sent_messages:
            send_time = sent_messages[msg_id]
            pick_up_time = response.get('pick_up_timestamp')
            response_time = response.get('response_timestamp')

            # Check if all timestamps are present
            if send_time and pick_up_time and response_time:
                pick_up_latency = pick_up_time - send_time
                processing_latency = response_time - pick_up_time
                total_latency = response_time - send_time
                metrics.append({
                    'message_id': msg_id,
                    'send_time': send_time,
                    'pick_up_time': pick_up_time,
                    'response_time': response_time,
                    'pick_up_latency': pick_up_latency,
                    'processing_latency': processing_latency,
                    'total_latency': total_latency,
                })

    if metrics:
        total_duration = max(m['response_time'] for m in metrics) - min(m['send_time'] for m in metrics)
        # total_pick_up_latency = sum(m['pick_up_latency'] for m in metrics)
        # total_processing_latency = sum(m['processing_latency'] for m in metrics)
        # total_total_latency = sum(m['total_latency'] for m in metrics)
        
        # directly calculate averages
        avg_pick_up_latency = sum(m['pick_up_latency'] for m in metrics) / len(metrics)
        avg_processing_latency = sum(m['processing_latency'] for m in metrics) / len(metrics)
        avg_total_latency = sum(m['total_latency'] for m in metrics) / len(metrics)

        print("\n--- Processing Metrics ---")
        print(f"Number of responses received: {len(responses)}/{num_messages}")
        print(f"Average Pick-Up Latency: {avg_pick_up_latency:.4f} seconds")
        print(f"Average Processing Latency: {avg_processing_latency:.4f} seconds")
        print(f"Average Total Latency (Send to Response): {avg_total_latency:.4f} seconds")
        print(f"Total Processing Time: {total_duration:.4f} seconds")
    else:
        print("\n--- No responses received or metrics could not be calculated. ---")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send messages to RabbitMQ for performance testing and collect response metrics.')
    # Key Parameters
    parser.add_argument('--num_messages', type=int, default=20, help='Number of messages to send')
    parser.add_argument('--timeout', type=int, default=60, help='How long to wait for response messages.')

    # Optional Parameters likely defauilts can be used
    parser.add_argument('--host', type=str, default='localhost', help='RabbitMQ host')
    parser.add_argument('--queue', type=str, default='request_queue', help='RabbitMQ queue name')
    parser.add_argument('--response_queue', type=str, default='response_queue', help='RabbitMQ response queue name.')

    args = parser.parse_args()

    send_messages(args.host, args.queue, args.num_messages, args.response_queue, args.timeout)
