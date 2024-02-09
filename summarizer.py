import argparse
import os
import textwrap
import yt_dlp
from whisper import init_whisper, transcribe_file
from gpt4 import summarize_GPT_4
import pandas as pd
from pydub import AudioSegment

with open ("current_video_file.dat", "r") as current_video_file:
    CURRENT_VIDEO_PROCCESSING = int(current_video_file.read())

def pretty_print(text, width):
    lines = text.splitlines()
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_text = '\n'.join(wrapped_lines)
    print(wrapped_text)

def download_audio(audio_filename, url):
    # Download from YouTube
    ydl_opts = {
        'outtmpl': audio_filename,
        'format': 'worstaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
def whisper_transcription(model, enc, chunk_filename):
    print("Transcribing ", chunk_filename, "...")
    output = transcribe_file(model, enc, chunk_filename)
    return output
    
def summarize_youtube(title, transcription):
    system_prompt = "You are a helpful assistant, whose sole job is to take transcripts and summarize them. You are helping your boss become rich and successful."
    summarize_prompt = f"Summarize the following transcript with a introduction and a list of 50 bullet points. I want to make a keynote out of the summary. Make it as useful as possible in the context of getting rich\n\n\nThis is the Text transcript: {transcription}:"
    response = summarize_GPT_4(system_prompt, summarize_prompt)
    summary = response.choices[0].message.content
    return summary

def chunk_big_file(audio_filename):
    audio = AudioSegment.from_mp3(audio_filename+".mp3")
    audio_length = len(audio) / 1000
    chunk_size = 1 * 60
    num_chunks = int(audio_length // chunk_size)
    remaining_time = audio_length % chunk_size

    for i in range(num_chunks):
        start_time = i * chunk_size
        end_time = (i + 1) * chunk_size
        chunk = audio[start_time * 1000:end_time * 1000]
        chunk.export(f"chunk_{i}.mp3", format="mp3")

    # Handle remaining time
    if remaining_time > 0:
        start_time = num_chunks * chunk_size
        end_time = start_time + remaining_time
        chunk = audio[start_time * 1000:end_time * 1000]
        chunk.export(f"chunk_{num_chunks}.mp3", format="mp3")
        num_chunks += 1

    return num_chunks

def cleanup(audio_filename, num_chunks):
    try:
        os.remove(audio_filename+".mp3")
        os.remove(audio_filename+"_mono.mp3")
    except:
        pass
    for i in range(num_chunks):
        try:
            os.remove(f"chunk_{i}.mp3")
        except:
            continue


def main_process_youtube_channel():
    youtube_videos = pd.read_csv("youtubeChannel.csv")
    for i in range(CURRENT_VIDEO_PROCCESSING, len(youtube_videos)):
        try:
            print("processing video ", i)
            url = youtube_videos["Video url"][i]
            video_title = youtube_videos["Video Title"][i].replace(" ", "_").replace(":", "_").replace("|", "_").replace("?", "_").replace("!", "_").replace(";", "_").replace(",", "_").replace(".", "_").replace("/", "_")
            if "temp" not in os.getcwd():
                os.chdir("./temp/")
            print("Donwloading audio from YouTube...")
            download_audio(video_title, url)
            print("chunking audio...")
            num_chunks = chunk_big_file(video_title)
            print("Initializing whisper...")
            model, enc = init_whisper("large-v2", batch_size=1)
            print("Transcribing audio... with", num_chunks, " chunks")
            for i in range(num_chunks):
                chunk_filename = f"chunk_{i}.mp3"
                try:
                    output = whisper_transcription(model, enc, chunk_filename)
                    with open(video_title+"_transcription.txt", "a") as text_file:
                        text_file.write(output)
                except:
                    continue
            print("Cleaning up...: ")
            cleanup(video_title, num_chunks)
            with open ("current_video_file.dat", "w") as current_video_file:
                current_video_file.write(str(i+1))
        except:
            main_process_youtube_channel()

def main():
    parser = argparse.ArgumentParser(description='Summarize YouTube videos.')
    parser.add_argument('--url', required=False, type=str, help='The URL of the YouTube video to summarize.')
    args = parser.parse_args()
    url = args.url
    if not url:
        url = input("Please enter the URL of the YouTube video to summarize: ")
    video_title = url.split("v=")[1]
    if "summaries" not in os.getcwd():
        os.chdir("./summaries/")
    print("Donwloading audio from YouTube...")
    download_audio(video_title, url)
    print("chunking audio...")
    num_chunks = chunk_big_file(video_title)
    print("Initializing whisper...")
    model, enc = init_whisper("large-v2", batch_size=1)
    print("Transcribing audio... with", num_chunks, " chunks")
    for i in range(num_chunks):
        chunk_filename = f"chunk_{i}.mp3"
        try:
            output = whisper_transcription(model, enc, chunk_filename)
            with open(video_title+"_transcription.txt", "a") as text_file:
                text_file.write(output)
        except:
            continue

    print("Summarizing with GPT-4...")
    with open (video_title+"_transcription.txt", "r") as file:
        data = file.read()
    summary = summarize_youtube(video_title, data)
    with open(video_title+"_summary.txt", "w") as text_file:
        text_file.write(summary)

    print("Cleaning up...: ")
    cleanup(video_title, num_chunks)

if __name__ == "__main__":
    main_process_youtube_channel()
    # main()