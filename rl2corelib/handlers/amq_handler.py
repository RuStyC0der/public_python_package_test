import os
import psutil
import ssl
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.sync import Stomp
from stompest.error import StompConnectionError, StompConnectTimeout
import time
import uuid
import codecs
from bson import BSON
import threading
import logging


class AMQHandler:
    def __init__(self, user_name, password, host, port=61614, queue_consumer='/queue/apiServer'):
        self.QUEUE_CONSUMER = queue_consumer
        self.host = host
        self.__CONFIG = self.__prepare_config(user_name, password, host, port)
        self.__events = []
        self._liveVideoCommands = ['liveVideoStart']
        self.subscribe = None
        self.client = None

    @staticmethod
    def __prepare_config(user_name, password, host, port):
        context = ssl.create_default_context()
        # Disable cert validation
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return StompConfig('failover:ssl://%s:%s' % (host, port),
                           sslContext=context, login=user_name, passcode=password, version=StompSpec.VERSION_1_1)

    def connect(self, subscribe=False, selector=None, msg='', with_logs=True, heart_beats=(30000, 30000)):
        self.subscribe = subscribe
        self.client = Stomp(self.__CONFIG)

        try:
            self.client.connect(heartBeats=heart_beats, versions=["1.1"])
        except (StompConnectionError, StompConnectTimeout) as e:
            logging.error('ActiveMQHandler: (StompConnectionError) reconnect. %s' % e)
            time.sleep(1)
            self.client.connect(heartBeats=heart_beats, versions=["1.1"])  # reconnect
        except Exception as e:
            logging.error('ActiveMQHandler: (StompConnectionError) reconnect2. %s' % e)

        if subscribe:
            headers = {
                StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                StompSpec.ID_HEADER: uuid.uuid4().hex
            }

            if selector:
                headers['selector'] = selector

            self.client.subscribe(self.QUEUE_CONSUMER, headers=headers)
        if with_logs:
            logging.info('ActiveMQHandler: %s is connected. %s' % ('Consumer' if subscribe else 'Sender', msg))

    def disconnect(self, msg='', with_logs=False):
        self.client.disconnect()
        if with_logs:
            conn_type = 'Consumer' if self.subscribe else 'Sender'
            logging.info('ActiveMQHandler: Disconnect %s, %s' % (conn_type, msg))

    @staticmethod
    def _encode_msg(msg_dict):
        return codecs.encode(BSON.encode(msg_dict), 'hex')

    @staticmethod
    def _decode_msg(mgs_hex):
        bson_obj = BSON(codecs.decode(mgs_hex, 'hex'))
        return dict(bson_obj.decode())

    def send_msg(self, queue_name, msg_dict, with_connect=True):
        logging.debug('ActiveMQHandler: %s, %s' % (queue_name, msg_dict))
        msq_hex = self._encode_msg(msg_dict)
        try:
            if with_connect:
                self.connect(with_logs=False)

            self.client.send(body=msq_hex, destination=queue_name)
            logging.debug('sendMsg to %s' % queue_name)
            if with_connect:
                self.disconnect(with_logs=False)
        except (StompConnectionError, StompConnectTimeout) as e:
            time.sleep(0.1)

            logging.error('ActiveMQHandler: sendMsg() sending error. %s' % e)
            self.connect(with_logs=False)
            self.client.send(body=msq_hex, destination=queue_name)
            logging.error('ActiveMQHandler: sendMsg() resend %s' % msg_dict)
        except Exception as e:
            logging.error('ActiveMQHandler: (Exception) sending error. %s' % e)

    def register_events(self, class_instance_or_list_funcs):
        if len(self.__events) > 0:
            return self.__events

        if not isinstance(class_instance_or_list_funcs, type) and not type(class_instance_or_list_funcs) is list:
            raise TypeError('expected class')

        methods_list = []

        if type(class_instance_or_list_funcs) is list:
            # noinspection PyTypeChecker
            for func in class_instance_or_list_funcs:
                if callable(func) and func.__name__.startswith("on"):
                    methods_list.append(func)
        else:
            class_obj = class_instance_or_list_funcs(self)
            for func in dir(class_instance_or_list_funcs):
                if callable(getattr(class_instance_or_list_funcs, func)) and func.startswith("on"):
                    methods_list.append(getattr(class_obj, func))

        self.__events = {f.__name__: f for f in methods_list}

    def _run_action(self, msg_dict, msg_header):
        action_name = list(msg_dict.keys())[0]
        method_name = 'on' + action_name[0].capitalize() + action_name[1:]

        if method_name in self.__events:
            server_name = msg_header['serverName'] if 'serverName' in msg_header else None
            return self.__events[method_name](msg_dict[action_name], server_name)
        else:
            logging.error('ActiveMQHandler: no message handler of %s' % method_name)
            raise ValueError('no message handler of %s' % method_name)

    def _receive_msg(self):
        can_read = self.client.canRead(0.8 * self.client.serverHeartBeat / 1000.0)  # poll server heart-beats
        # logging.info(f'can_read is {can_read}')
        self.client.beat()  # send client heart-beat

        if can_read:
            logging.info('Try to receive frame')
            frame = self.client.receiveFrame()

            if not frame.body:
                return frame, None, None

            msg_dict = {}
            try:
                msg_dict = self._decode_msg(frame.body)
                cb_resp = self._run_action(msg_dict, frame.headers)

                return frame, msg_dict, cb_resp
            except ValueError as e:
                logging.error(f'ActiveMQHandler: {e}')
                return None, None, None
            except Exception as e:
                logging.error('ActiveMQHandler: Error processing message. Mq data %s. Exception: %s' % (msg_dict, e))
                return None, None, None

        return None, None, None

    def __start_consuming(self, disable_selector=False):
        max_count_to_reconnect = 2
        while True:
            logging.info('Try1')
            try:
                if disable_selector:
                    selector = None
                else:
                    selector = "actionName IS NULL OR actionName NOT IN ('%s')" % ("','".join(self._liveVideoCommands))
                self.connect(subscribe=True, selector=selector, msg='Func startConsuming()')
                count_to_reconnect = 0
                while True:
                    logging.info('Try2')
                    frame, msg_dict, event_result = self._receive_msg()
                    if frame:
                        count_to_reconnect = 0
                        if event_result is not None:
                            logging.debug(f'Remove item from queue, event result is "{event_result}"')
                            self.client.ack(frame)
                            time.sleep(0.01)
                        # Show memory usage
                        process = psutil.Process(os.getpid())
                        logging.debug(f'Use memory: {process.memory_info().rss / 1000} KB')
                    else:
                        count_to_reconnect += 1
                    if count_to_reconnect >= max_count_to_reconnect:
                        self.disconnect(msg='queue stuck', with_logs=True)
                        time.sleep(5)
                        break
                if count_to_reconnect < max_count_to_reconnect:
                    logging.error('Internal cycle has been stopped')
            except Exception as e:
                # Disconnect on exception
                logging.error('ActiveMQHandler: Reconnecting...\nDetail:\n%s' % e)
                try:
                    self.disconnect('Func startConsuming()', with_logs=True)
                except Exception as ex:
                    logging.error(f'ActiveMQHandler: Disconnection error, {ex}')
                time.sleep(5)

    def start_consuming(self, enable_threading=False, disable_selector=False):
        if enable_threading:
            thread = threading.Thread(target=self.__start_consuming, args=(disable_selector,))
            thread.setDaemon(True)
            thread.start()
            time.sleep(1)
        else:
            self.__start_consuming(disable_selector)
