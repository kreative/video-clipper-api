import json
import os

import httpx
from deepgram import DeepgramClient, PrerecordedOptions
from flask import current_app as app
from openai import OpenAI
from pytubefix import YouTube

from src.aws.sqs import sqs_client
from src.db import db
from src.models import Video
from src.utils.resiliance import retry_on_db_error, retry_with_exp_backoff

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
gpt = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def convert_keywords_to_string(keywords):
    return ",".join(keywords)


@retry_on_db_error
def get_videos_for_user(user_id):
    return Video.query.filter_by(user_id=user_id).all()


@retry_on_db_error
def get_video_by_id(video_id):
    if not video_id:
        return None

    return db.session.get(Video, video_id)


@retry_on_db_error
def add_new_video(user_id, link):
    if not link.startswith("https://www.youtube.com"):
        raise ValueError("Invalid YouTube Link")

    try:
        yt = YouTube(link)
    except Exception:
        raise ValueError("Connection Error")

    video_info = get_video_info(yt)
    keywords = convert_keywords_to_string(video_info["keywords"])

    new_video = Video(
        user_id=user_id,
        yt_link=link,
        status="pending",
        title=video_info["title"],
        length=video_info["length"],
        views=str(video_info["views"]),
        thumbnail_url=video_info["thumbnail_url"],
        description=video_info["description"],
        keywords=keywords,
        rating=video_info["rating"],
        author=video_info["author"],
        channel_url=video_info["channel_url"],
        transcript=None,
        prompt_response=None,
    )

    db.session.add(new_video)
    db.session.commit()

    return new_video


@retry_on_db_error
def update_video(video_id, transcript, prompt_response, status):
    video = get_video_by_id(video_id)

    if not video:
        raise ValueError("Invalid Video ID")

    if transcript:
        video.transcript = transcript

    if prompt_response:
        video.prompt_response = prompt_response

    if status:
        video.status = status

    db.session.commit()

    return video


@retry_on_db_error
def delete_video(video_id):
    video = get_video_by_id(video_id)

    if not video:
        raise ValueError("Invalid Video ID")

    db.session.delete(video)
    db.session.commit()

    return video


def get_video_info(yt) -> dict:
    return {
        "title": yt.title,
        "length": yt.length,
        "views": yt.views,
        "age_restricted": yt.age_restricted,
        "thumbnail_url": yt.thumbnail_url,
        "description": yt.description,
        "keywords": yt.keywords,
        "rating": yt.rating,
        "author": yt.author,
        "channel_url": yt.channel_url,
    }


def download_video_as_mp4(yt):
    try:
        yt = YouTube(yt)
    except Exception as e:
        app.logger.error(e)
        return "Conection Error", 500

    project_dir = os.path.abspath(os.path.dirname(__file__))
    save_path = project_dir + "/tmp_video_downloads"
    mp4_streams = yt.streams.filter(file_extension="mp4")
    d_video = mp4_streams[-1]

    try:
        d_video.download(output_path=save_path)
    except Exception as e:
        print(e)
        print("Some Error!")

    return f"{save_path}/{yt.title}.m4a"


def remove_downloaded_video(file_path):
    os.remove(file_path)


@retry_with_exp_backoff
def transcribe_audio(file_path):
    buffer_data = None

    with open(file_path, "rb") as file:
        buffer_data = file.read()

    payload = {"buffer": buffer_data}

    options = PrerecordedOptions(smart_format=True, punctuate=True)

    response = deepgram.listen.rest.v("1").transcribe_file(
        payload,
        options,
        timeout=httpx.Timeout(300.0, connect=10.0),
    )

    return response["results"]["channels"][0]["alternatives"][0]["transcript"]


def summarize_text(transcript, prompt):
    response = gpt.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        model="gpt-4o",
    )

    return response.choices[0].message.content


def send_message(video_id, yt_link):
    print("Sending message to SQS")
    print(video_id)
    print(yt_link)

    sqs_client.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/485069184701/video-clipper",
        MessageBody=json.dumps({ "yt_link": yt_link, "video_id": video_id }),
        DelaySeconds=0,
    )


def process_video_message(message):
    body = json.loads(message.get("Body"))
    yt_link = body["yt_link"]
    video_id = body["video_id"]

    print(f"Processing {video_id}")

    path = download_video_as_mp4(yt_link)

    print(path)

    transcript = transcribe_audio(path)

    print(transcript)

    remove_downloaded_video(path)

    print("Deleted video")

    prompt = f"Summarize the following transcript: {transcript}"

    print(prompt)

    summary = summarize_text(transcript, prompt)

    print(summary)

    updated_video = update_video(
        video_id=video_id,
        transcript=transcript,
        prompt_response=summary,
        status="completed",
    )

    print(updated_video)

    return True
