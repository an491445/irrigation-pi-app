import mqtt
import time
import schedule
import devices
from worker import Worker
import json
from utils import json_dumps
import queue
import logging
from config import LOG_FORMAT, LOG_LEVEL, LOG_FILENAME

def main_loop():
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, LOG_LEVEL),
        handlers=[
            logging.FileHandler(LOG_FILENAME),
            logging.StreamHandler()
        ]
    )

    logging.info("###############")
    logging.info("Starting irrigation system...")

    # Set up devices
    d = devices.init()

    # Connect to MQTT broker
    client = mqtt.connect()

    # Job queue
    work_queue = Worker(d, client)

    def read_sensors():
        work_queue.append("read_sensors")

    def handle_request(client, userdata, message):
        try:
            payload = json.loads(message.payload)
            logging.info("Got new request: {}".format(payload))
            work_queue.append("handle_request", payload)
            client.publish('pi/events', json_dumps({
                **payload,
                "status": "queued",
            }))
        except queue.Full:
            if payload:
                client.publish('pi/events', json_dumps({
                    **payload,
                    "status": "rejected",
                    "message": "Too many jobs in queue",
                }))
        except Exception as e:
            logging.warning('Could not handle incoming request')
            logging.warning(e, exc_info=True)

    def cancel_jobs(client, userdata, message):
        logging.info('Got abort message')
        # No need to look at the message, just clean work queue and close everything...
        work_queue.cancel()

    # Handle incoming requests
    client.message_callback_add("pi/requests", handle_request)

    # Abort...
    client.message_callback_add("pi/abort", cancel_jobs)

    # Scheduled jobs
    schedule.every(15 * 60).seconds.do(read_sensors)

    # Process MQTT events on another thread
    client.loop_start()
    logging.info("App ready")

    try:
        while True:
            # Add scheduled jobs to queue
            schedule.run_pending()
            # Pop queue
            work_queue.work()
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info('Process ended by user.')

    except Exception as e:
        logging.critical(e, exc_info=True)

    finally:
        if d:
            logging.info('Shutting down gracefully...')
            if client:
                d.disconnect(client)
            else:
                d.disconnect()
        if client:
            logging.info('Killing MQTT thread...')
            client.loop_stop()

if __name__ == '__main__':
    main_loop()
