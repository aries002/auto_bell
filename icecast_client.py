import ctypes
import ffmpeg
import numpy as np
from openal.al import *
from openal.alc import *
from queue import Queue, Empty
from threading import Thread
import time
from urllib.request import urlopen

def init_audio():
    #Create an OpenAL device and context.
    device_name = alcGetString(None, ALC_DEFAULT_DEVICE_SPECIFIER)
    device = alcOpenDevice(device_name)
    context = alcCreateContext(device, None)
    alcMakeContextCurrent(context)
    return (device, context)

def create_audio_source():
    #Create an OpenAL source.
    source = ctypes.c_uint()
    alGenSources(1, ctypes.pointer(source))
    return source

def create_audio_buffers(num_buffers):
    #Create a ctypes array of OpenAL buffers.
    buffers = (ctypes.c_uint * num_buffers)()
    buffers_ptr = ctypes.cast(
        ctypes.pointer(buffers), 
        ctypes.POINTER(ctypes.c_uint),
    )
    alGenBuffers(num_buffers, buffers_ptr)
    return buffers_ptr

def fill_audio_buffer(buffer_id, chunk):
    #Fill an OpenAL buffer with a chunk of PCM data.
    alBufferData(buffer_id, AL_FORMAT_STEREO16, chunk, len(chunk), 44100)

def get_audio_chunk(process, chunk_size):
    #Fetch a chunk of PCM data from the FFMPEG process.
    return process.stdout.read(chunk_size)

def play_audio(process):
    #Queues up PCM chunks for playing through OpenAL
    num_buffers = 4
    chunk_size = 8192
    device, context = init_audio()
    source = create_audio_source()
    buffers = create_audio_buffers(num_buffers)

    #Initialize the OpenAL buffers with some chunks
    for i in range(num_buffers):
        buffer_id = ctypes.c_uint(buffers[i])
        chunk = get_audio_chunk(process, chunk_size)
        fill_audio_buffer(buffer_id, chunk)

    #Queue the OpenAL buffers into the OpenAL source and start playing sound!
    alSourceQueueBuffers(source, num_buffers, buffers)
    alSourcePlay(source)
    num_used_buffers = ctypes.pointer(ctypes.c_int())

    while True:
        #Check if any buffers are used up/processed and refill them with data.
        alGetSourcei(source, AL_BUFFERS_PROCESSED, num_used_buffers)
        if num_used_buffers.contents.value != 0:
            used_buffer_id = ctypes.c_uint()
            used_buffer_ptr = ctypes.pointer(used_buffer_id)
            alSourceUnqueueBuffers(source, 1, used_buffer_ptr)
            chunk = get_audio_chunk(process, chunk_size)
            fill_audio_buffer(used_buffer_id, chunk)
            alSourceQueueBuffers(source, 1, used_buffer_ptr)

def init(url=""):
# if __name__ == "__main__":    
#     url = "http://192.168.7.8:8000/radio.mp3"

    #Run FFMPEG in a separate process using subprocess, so it is non-blocking
    process = (
        ffmpeg
        .input(url)
        .output("pipe:", format='s16le', acodec='pcm_s16le', ac=2, ar=44100, loglevel="quiet")
        .run_async(pipe_stdout=True)
    )

    #Run audio playing OpenAL code in a separate thread
    thread = Thread(target=play_audio, args=(process,), daemon=True)
    thread.start()

    # #Some example code to show that this is not being blocked by the audio.
    # start = time.time()
    # while True:
    #     print(time.time() - start)