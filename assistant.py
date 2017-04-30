import logging
import os
import snowboydecoder

import click
from google.assistant.embedded.v1alpha1 import embedded_assistant_pb2
from google.rpc import code_pb2

from googlesamples.assistant import (
    assistant_helpers,
    audio_helpers,
    auth_helpers,
    common_settings
)


class Assistant:
    ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
    END_OF_UTTERANCE = embedded_assistant_pb2.ConverseResponse.END_OF_UTTERANCE
    DIALOG_FOLLOW_ON = embedded_assistant_pb2.ConverseResult.DIALOG_FOLLOW_ON
    CLOSE_MICROPHONE = embedded_assistant_pb2.ConverseResult.CLOSE_MICROPHONE

    def __init__(self):
        self.api_endpoint = Assistant.ASSISTANT_API_ENDPOINT
        self.credentials = os.path.join(
            click.get_app_dir(common_settings.ASSISTANT_APP_NAME),
            common_settings.ASSISTANT_CREDENTIALS_FILENAME
        )
        self.verbose = False
        self.audio_sample_rate = common_settings.DEFAULT_AUDIO_SAMPLE_RATE
        self.audio_sample_width = common_settings.DEFAULT_AUDIO_SAMPLE_WIDTH
        self.audio_iter_size = common_settings.DEFAULT_AUDIO_ITER_SIZE
        self.audio_block_size = common_settings.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE
        self.audio_flush_size = common_settings.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
        self.grpc_deadline = common_settings.DEFAULT_GRPC_DEADLINE

        # Setup logging.
        logging.basicConfig() # filename='assistant.log', level=logging.DEBUG if self.verbose else logging.INFO)

        self.logger = logging.getLogger("assistant")
        self.logger.setLevel(logging.DEBUG)
        self.creds = auth_helpers.load_credentials(
            self.credentials, scopes=[common_settings.ASSISTANT_OAUTH_SCOPE]
        )

        # Create gRPC channel
        grpc_channel = auth_helpers.create_grpc_channel(
            self.api_endpoint, self.creds
        )
        self.logger.info('Connecting to %s', self.api_endpoint)
        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2.EmbeddedAssistantStub(grpc_channel)

        # Stores an opaque blob provided in ConverseResponse that,
        # when provided in a follow-up ConverseRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Converse()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state_bytes = None

        # Stores the current volument percentage.
        # Note: No volume change is currently implemented in this sample
        self.volume_percentage = 50

    def assist(self):

        # Configure audio source and sink.
        self.audio_device = None
        self.audio_source = self.audio_device = (
            self.audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=self.audio_sample_rate,
                sample_width=self.audio_sample_width,
                block_size=self.audio_block_size,
                flush_size=self.audio_flush_size
            )
        )

        self.audio_sink = self.audio_device = (
            self.audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=self.audio_sample_rate,
                sample_width=self.audio_sample_width,
                block_size=self.audio_block_size,
                flush_size=self.audio_flush_size
            )
        )

        # Create conversation stream with the given audio source and sink.
        self.conversation_stream = audio_helpers.ConversationStream(
            source=self.audio_source,
            sink=self.audio_sink,
            iter_size=self.audio_iter_size,
        )
        restart = False
        continue_dialog = True
        try:
            while continue_dialog:
                continue_dialog = False
                # snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)
                self.conversation_stream.start_recording()
                self.logger.info('Recording audio request.')

                # This generator yields ConverseResponse proto messages
                # received from the gRPC Google Assistant API.
                for resp in self.assistant.Converse(self._iter_converse_requests(),
                                                    self.grpc_deadline):
                    assistant_helpers.log_converse_response_without_audio(resp)
                    if resp.error.code != code_pb2.OK:
                        self.logger.error('server error: %s', resp.error.message)
                        break
                    if resp.event_type == Assistant.END_OF_UTTERANCE:
                        self.logger.info('End of audio request detected')
                        self.conversation_stream.stop_recording()
                    if resp.result.spoken_request_text:
                        self.logger.info('Transcript of user request: "%s".',
                                     resp.result.spoken_request_text)
                        self.logger.info('Playing assistant response.')
                    if len(resp.audio_out.audio_data) > 0:
                        self.conversation_stream.write(resp.audio_out.audio_data)
                    if resp.result.spoken_response_text:
                        self.logger.info(
                            'Transcript of TTS response '
                            '(only populated from IFTTT): "%s".',
                            resp.result.spoken_response_text)
                    if resp.result.conversation_state:
                        self.conversation_state_bytes = resp.result.conversation_state
                    if resp.result.volume_percentage != 0:
                        volume_percentage = resp.result.volume_percentage
                        self.logger.info('Volume should be set to %s%%', volume_percentage)
                    if resp.result.microphone_mode == self.DIALOG_FOLLOW_ON:
                        continue_dialog = True
                        self.logger.info('Expecting follow-on query from user.')
                self.logger.info('Finished playing assistant response.')
                self.conversation_stream.stop_playback()
        except Exception as e:
            self._create_assistant()
            self.logger.exception('Skipping because of connection reset')
            restart = True
        try:
            self.conversation_stream.close()
            if restart:
                self.assist()
        except Exception:
            self.logger.error('Failed to close conversation_stream.')

    def _create_assistant(self):
        # Create gRPC channel
        grpc_channel = auth_helpers.create_grpc_channel(
            self.api_endpoint, self.creds
        )
        self.logger.info('Connecting to %s', self.api_endpoint)
        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2.EmbeddedAssistantStub(grpc_channel)

    # This generator yields ConverseRequest to send to the gRPC
    # Google Assistant API.
    def _gen_converse_requests(self):
        converse_state = None
        if self.conversation_state_bytes:
            self.logger.debug('Sending converse_state: %s',
                          self.conversation_state_bytes)
            converse_state = embedded_assistant_pb2.ConverseState(
                conversation_state=self.conversation_state_bytes,
            )
        config = embedded_assistant_pb2.ConverseConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=int(self.audio_sample_rate),
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=int(self.audio_sample_rate),
                volume_percentage=self.volume_percentage,
            ),
            converse_state=converse_state
        )
        # The first ConverseRequest must contain the ConverseConfig
        # and no audio data.
        yield embedded_assistant_pb2.ConverseRequest(config=config)
        for data in self.conversation_stream:
            # Subsequent requests need audio data, but not config.
            yield embedded_assistant_pb2.ConverseRequest(audio_in=data)

    def _iter_converse_requests(self):
        for c in self._gen_converse_requests():
            assistant_helpers.log_converse_request_without_audio(c)
            yield c
        self.conversation_stream.start_playback()
