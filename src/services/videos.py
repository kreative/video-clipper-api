import os

import httpx
from deepgram import DeepgramClient, PrerecordedOptions
from openai import OpenAI
from pytubefix import YouTube

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
    if not YouTube.validate_link(link):
        raise ValueError("Invalid YouTube Link")

    try:
        yt = YouTube(link)
    except Exception as e:
        app.logger.error(e)
        raise ValueError("Connection Error")

    video_info = get_video_info(yt)

    new_video = Video(
        user_id=user_id,
        yt_link=link,
        status="pending",
        title=video_info["title"],
        length=video_info["length"],
        views=video_info["views"],
        thumbnail_url=video_info["thumbnail_url"],
        description=video_info["description"],
        keywords=convert_keywords_to_string(video_info["keywords"]),
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
def update_video(video_id, **kwargs):
    video = get_video_by_id(video_id)

    if not video:
        raise ValueError("Invalid Video ID")

    for key, value in kwargs.items():
        if hasattr(video, key):
            setattr(video, key, value)

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
        yt = YouTube(link)
    except Exception as e:
        app.logger.error(e)
        return "Conection Error", 500

    save_path = "/tmp_video_downloads"
    mp4_streams = yt.streams.filter(file_extension="mp4")
    d_video = mp4_streams[-1]

    try:
        d_video.download(output_path=save_path)
    except Exception as e:
        print(e)
        print("Some Error!")

    return f"{save_path}/{yt.title}.m4a"


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
