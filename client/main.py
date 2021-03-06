
from libs.config_service import ConfigService
from libs.effects import Effects
from libs.effects_enum import EffectsEnum
from libs.notification_enum import NotificationEnum
from libs.notification_service import NotificationService
from libs.server_service import ServerService
from libs.audio_process_service import AudioProcessService

import numpy as np
from multiprocessing import Process, Queue, Manager, Lock
from time import sleep

class Main():
    """
    This is the main class. It control everything.
    Its the first starting point of the programm.
    """

    def start(self):
        """
        This function will start all neccesary components.
        Let's go :-D
        """
        
        print("Init the programm...")

        # We need a lock to prevent too fast save and load actions of the config
        self._config_lock = Lock()

        # Create the instance of the config
        self._config_instance = ConfigService.instance(self._config_lock)
        self._config = self._config_instance.config        

        # Prepare the queue for the output
        self._effects_queue = Queue(2)
        self._audio_queue_lock = Lock()
        self._audio_queue = Queue(2)
        self._server_queue_lock = Lock()
        self._server_queue = Queue(2)

        # Prepare all notification queues
        self._notification_queue_effects_in = Queue(2)
        self._notification_queue_effects_out = Queue(2)

        self._notification_queue_audio_in = Queue(2)
        self._notification_queue_audio_out = Queue(2)

        self._notification_queue_server_in = Queue(2)
        self._notification_queue_server_out = Queue(2)

         # Start Notification Service
        self._notification_service = NotificationService()
        self._notification_service_process = Process(
            target=self._notification_service.start, 
            args=(
                self._config_lock, 
                self._notification_queue_effects_in, 
                self._notification_queue_effects_out, 
                ))
        self._notification_service_process.start()
        

        #Start Server
        self._server = ServerService()
        self._server_process = Process(
            target=self._server.start, 
            args=(
                self._config_lock, 
                self._notification_queue_server_in, 
                self._notification_queue_server_out,
                self._server_queue,
                self._server_queue_lock
                ))
        self._server_process.start()


        # Start the Effect Service
        self._effects = Effects()
        self._effects_process = Process(
            target=self._effects.start, 
            args=(
                self._config_lock, 
                self._notification_queue_effects_in, 
                self._notification_queue_effects_out, 
                self._effects_queue,
                self._server_queue,
                self._server_queue_lock,
                self._audio_queue,
                self._audio_queue_lock
                
                ))
        self._effects_process.start()


        #Start audio process
        self._audio = AudioProcessService()
        self._audio_process = Process(
            target=self._audio.start, 
            args=(
                self._config_lock, 
                self._notification_queue_server_in, 
                self._notification_queue_server_out,
                self._audio_queue,
                self._audio_queue_lock
                ))
        self._audio_process.start()


       
        

        print("Init finished")

        try:

            print("Programm started...")

            self._cancel_token = False

            # Do nothing with this thread. Just wait for the exit.
            while not self._cancel_token:
                sleep(10)
        
        except KeyboardInterrupt:
            print("Stop the programm...")
            
            self._server_process.terminate()
            self._effects_process.terminate()
            self._audio_process.terminate()
            self._notification_service_process.terminate()

            print("Programm stopped")


if __name__ == "__main__":

    main = Main()
    main.start()