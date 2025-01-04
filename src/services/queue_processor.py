from src.aws.sqs import sqs_client


class QueueProcessor:
    def __init__(self, queue_url: str, dlq_url: str, processor_func):
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.processor_func = processor_func

    def process_message(self, message) -> str:
        try:
            is_processed = self.processor_func(message)

            if not is_processed:
                self._move_to_dlq(message)

            self._delete_message(message)

            if is_processed:
                return f"Message processed successfully, {message.get('MessageId')}"
            else:
                return f"Message failed, {message.get('MessageId')}, moved to dlq"
        except Exception as e:
            self._move_to_dlq(message)
            return f"""Message failed, {message.get('MessageId')}, moved to dlq, error: {str(e)}"""

    def _move_to_dlq(self, message) -> None:
        sqs_client.send_message(QueueUrl=self.dlq_url, MessageBody=message["Body"])
        self._delete_message(message)

    def _delete_message(self, message) -> None:
        sqs_client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=message["ReceiptHandle"])

    def receive_messages(self):
        return sqs_client.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5)
