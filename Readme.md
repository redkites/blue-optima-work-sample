# Performance Optimization Worksample BlueOptima Python Engineer

## Problem Outline

This worksample focuses on improving the performance of a Python application that processes messages from a RabbitMQ queue. The application currently performs the following steps for each message:

1.  Receives a message from a RabbitMQ queue.
2.  Performs a some preprocessing operation that includes both a simulated I/O-bound delay and a data transformation.
3.  Passes the result of the preprocessing operation to an ONNX model for inference.
4.  Returns the result.

Your task is to analyze the existing application and identify performance bottlenecks. You are expected to make changes to the application to significantly improve its throughput and/or reduce latency. You should consider using concurrency techniques such as threading or asynchronous programming to achieve these improvements.

## Setup and Running the Application

Follow these steps to set up and run the application on your local machine:

**Prerequisites:**

* Docker installed on your system.
* Python 3.9 or higher installed (though Docker will handle the application environment).
* `pip` installed (usually comes with Python).

**Steps:**

1.  **Clone the Repository:** Obtain the code for this worksample (you will be provided with a link to the repository).

2.  **Navigate to the Project Directory:** Open your terminal or command prompt and navigate to the root directory of the cloned repository.

3.  **Build the Docker Image:**
    ```bash
    docker build -t python-worker .
    ```
    This command will build a Docker image named `python-worker` using the `dockerfile` in the current directory.

4.  **Run RabbitMQ:**
    ```bash
    docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3.9-alpine
    ```
    This command will start a RabbitMQ container named `rabbitmq` in detached mode. The RabbitMQ management interface will be accessible on port 5672 of your localhost.

5.  **Run the Worker Application:**
    ```bash
    docker run -d --name worker --link --cpus 1 -m 512m rabbitmq:rabbitmq python-worker
    ```
    This command will run the worker application within a Docker container named `worker`. The `--link` option ensures that the worker container can communicate with the RabbitMQ container using the hostname `rabbitmq`. You can view the logs of the worker application using:
    ```bash
    docker logs worker -f
    ```

## Testing the Application

A testing script (`test_script.py`) is provided to generate a large number of messages and send them to the RabbitMQ queue.

**Steps:**

1.  **Install `pika` (if you haven't already):**
    ```bash
    pip install pika
    ```

2.  **Run the Test Script:**
    ```bash
    python test_script.py --host localhost --num_messages 1000
    ```
    You can adjust the `--host` (if your RabbitMQ is running elsewhere) and `--num_messages` to control the number of messages sent. The script will output the total time taken to send the messages and the average send time per message.

3.  **Observe the Worker Logs:** While the test script is running, observe the logs of the worker application (`docker logs worker -f`) to see how it processes the messages.

4.  **Measure Performance After Your Changes:** After you have made your performance improvements, run the test script again and compare the time taken to process the same number of messages. You should also observe the worker logs to see the impact of your changes.

## Clean docker images and containers

The following steps will help you to remove the containers from your machine.

**Steps:**

1.  **Stop Worker:**
    ```bash
    docker stop worker
    ```

2.  **Stop RabbitMQ:**
    ```bash
    docker stop rabbitmq
    ```

3.  **Remove Worker:**
    ```bash
    docker rm worker
    ```

4.  **Remove RabbitMQ:**
    ```bash
    docker rm rabbitmq
    ```

### Restarting Rabbitmq

You can always clear the messages in RabbitMQ but restarting the queue:
  ```bash
  docker restart rabbitmq
  ```

## Hints and Suggestions

Here are some hints and suggestions to guide you in improving the performance of the application, there is no need to do all of these to produce a great solution:

* **Identify Bottlenecks:** Carefully examine the application, consider adding better logs to make it easier to see the impacts.
* **Concurrency:** Consider using Python's concurrency features to handle multiple messages concurrently.
    * **Threading (`threading` module):** Might be suitable for the CPU-bound part of the `preprocessing_operation` or for handling multiple incoming messages. Be mindful of the Global Interpreter Lock (GIL) for purely CPU-bound tasks in CPython.
    * **Asynchronous Programming (`asyncio` module):** Could be beneficial for the simulated I/O-bound operation (the `time.sleep`).
    * **Multiprocessing (`multiprocessing` module):** Can be used to leverage multiple CPU cores by creating separate processes. This is often a good choice for CPU-bound tasks as it bypasses the GIL.
* **RabbitMQ Blocking:** The current RabbitMQ interaction in `app/main.py` using the `pika` library is likely blocking. Explore non-blocking alternatives or ways to handle multiple consumers.
* **ONNX Model Loading:** Think about how the ONNX model is loaded and used within the `app/main.py`. If you process many messages concurrently, ensure this process is efficient and doesn't introduce new bottlenecks.
* **Resource Management:** Consider how your changes might impact resource usage (CPU, memory).

## Things Not To Do (Potential Pitfalls)

Here are a few things to consider and potentially avoid:

* **Premature Optimization:** While the goal is performance improvement, make sure your changes are based on understanding the bottlenecks rather than just guessing.
* **Not Validating the Impacts:** The optimizations you make to the application should be able to be justified and backed up by the metrics some have already be provided.
* **Not Acknowledging Messages:** Ensure that your worker application correctly acknowledges messages from RabbitMQ after processing them to prevent messages from being lost. The current code in `app/main.py` does this.
* **Overcomplicating the Solution:** Aim for a solution that is efficient but also maintainable and easy to understand. Don't introduce unnecessary complexity.
* **Not Testing Thoroughly:** After making changes, thoroughly test your application with a significant number of messages to ensure that the performance has indeed improved and that no new issues have been introduced.

We look forward to seeing your approach to improving the performance of this application!
