import threading
import time
from typing import List

from flask import Flask

from src.services.queue_processor import QueueProcessor
from src.services.videos import process_video_message

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/485069184701/video-clipper"
DLQ_URL = "https://sqs.us-east-1.amazonaws.com/485069184701/video-clipper-dlq"

class SQSConsumer:
    def __init__(self, app: Flask):
        self.app = app
        self.should_continue = threading.Event()
        self.should_continue.set()
        self.threads: List[threading.Thread] = []
        self.processors = [QueueProcessor(QUEUE_URL, DLQ_URL, process_video_message)]

    def consume_queue(self, processor: QueueProcessor) -> None:
        with self.app.app_context():
            while self.should_continue.is_set():
                response = processor.receive_messages()

                if "Messages" in response:
                    for message in response["Messages"]:
                        report = processor.process_message(message)
                        self.app.logger.info(report)
                else:
                    time.sleep(2)

    def start(self) -> None:
        self.app.logger.info("Starting SQS consumer threads")
        for processor in self.processors:
            thread = threading.Thread(target=self.consume_queue, args=(processor,))
            thread.start()
            self.threads.append(thread)
        self.app.logger.info("SQS consumer threads started")

    def stop(self) -> None:
        self.app.logger.info("Stopping SQS consumer threads")
        self.should_continue.clear()
        for thread in self.threads:
            thread.join()
        self.app.logger.info("SQS consumer threads stopped")
