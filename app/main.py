import pika
import json
import time
import asyncio
from typing import Dict, List, Any
from lib.utils import preprocessing_operations
from lib.model_inference import ONNXModelWrapper

RABBITMQ_HOST = "localhost"  # Assuming your RabbitMQ container is named 'rabbitmq' in Docker
QUEUE_NAME = "request_queue"
ONNX_MODEL_PATH = "model.onnx"  # Ensure this path is correct within the container

async def process_message(message_body: str, model_wrapper: ONNXModelWrapper) -> Dict[str, Any]:
    """
    Processes a single message from the queue asynchronously.
    """
    data: Dict[str, Any] = json.loads(message_body)
    input_data: List[float] = data.get("data", [])
    processed_data = await preprocessing_operations(input_data)  # Ensure this is awaited
    model_output = model_wrapper.predict(processed_data)
    result = {"original_input": input_data, "processed_data": processed_data, "model_output": model_output}
    return result

async def callback(ch, method, properties, body, model_wrapper: ONNXModelWrapper) -> None:
    """
    Callback function to process messages from RabbitMQ asynchronously.
    """
    try:
        message_body = body.decode()
        data = json.loads(message_body)
        message_id = data.get("message_id")  # Extract the message_id from the incoming message
        pick_up_timestamp = time.time()  # Record the time the message was picked up
        result = await process_message(message_body, model_wrapper)
        response_message = json.dumps({
            "message_id": message_id,  # Include the message_id in the response
            "original_input": result["original_input"],
            "processed_data": result["processed_data"],
            "model_output": result["model_output"],
            "pick_up_timestamp": pick_up_timestamp,
            "response_timestamp": time.time()  # Record the time the response is sent
        })
        print(f"Publishing response to queue '{properties.reply_to}': {response_message}")  # Debugging log
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,  # Ensure this matches the response queue
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=response_message
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message {message_id}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) #removed multiple=False to avoid requeueing

async def main() -> None:
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=10)  # Allow up to 10 messages to be processed concurrently

    model_wrapper = ONNXModelWrapper(ONNX_MODEL_PATH)

    print("Ready to receive messages")
    loop = asyncio.get_event_loop()
    try:
        while True:
            method, properties, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
            if body:
                loop.create_task(callback(channel, method, properties, body, model_wrapper))
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print("Terminating application...")
    finally:
        connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application interrupted by user")