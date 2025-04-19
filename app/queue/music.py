import asyncio
import json
from pathlib import Path

import aiofiles
import httpx
from yt_dlp.utils import sanitize_filename

from app.channels import MUSIC_JOB_UPDATE
from app.clients import audiotags, ffmpeg, imagedownloader, invidious, s3, ytdlp
from app.db.models.musicjob import MusicJob, MusicJobRespository
from app.models.music import MusicJobUpdateResponse
from app.queue.context import SAQContext
from app.services import tempfiles
from app.settings import settings
from app.utils.youtube import parse_youtube_video_id

JOB_DIR = "music_jobs"


async def retrieve_audio_file(music_job: MusicJob):
    jobs_root_directory = await tempfiles.create_new_directory(JOB_DIR)
    job_file_path = Path(jobs_root_directory).joinpath(JOB_DIR)
    filename = None
    if music_job.filename_url:
        async with httpx.AsyncClient() as client:
            client.stream()
            response = await client.get(music_job.filename_url)
            audio_file_path = job_file_path.joinpath(
                f"temp{Path(music_job.original_filename).suffix}"
            )

            async with aiofiles.open(audio_file_path, mode="wb") as f:
                await f.write(response.content)

            filename = await ffmpeg.convert_audio_to_mp3(audio_file=audio_file_path)
    elif music_job.video_url:
        if "youtube.com" in music_job.video_url:
            video_id = parse_youtube_video_id(music_job.video_url)
            audio_file_path = Path(job_file_path).joinpath("temp.audio")
            await invidious.download_audio_from_youtube_video(
                video_id=video_id, download_path=audio_file_path
            )
            filename = await ffmpeg.convert_audio_to_mp3(audio_file=audio_file_path)
        else:
            filename = Path(job_file_path).joinpath("temp.mp3")
            await ytdlp.download_audio_from_video(
                url=music_job.video_url, download_path=f"{Path(filename).stem}"
            )
    return filename


def update_audio_tags(
    music_job: MusicJob,
    filename: str,
    artwork_info: imagedownloader.RetrievedArtwork,
):
    audio_tag_service = audiotags.AudioTags(file_path=filename)
    audio_tag_service.title = music_job.title
    audio_tag_service.artist = music_job.artist
    audio_tag_service.album = music_job.album
    if music_job.grouping:
        audio_tag_service.grouping = music_job.grouping
    if artwork_info:
        audio_tag_service.set_artwork(
            data=artwork_info.image,
            mime_type=f"image/{artwork_info.extension}",
        )


async def run_music_job(ctx: SAQContext, music_job_id: str):
    redis = ctx["redis"]
    sessionmaker = ctx["db_sessionmaker"]
    async with sessionmaker() as session:
        music_jobs_repo = MusicJobRespository(session=session)
        music_job = await music_jobs_repo.get_one(MusicJob.id == music_job_id)
        await redis.publish(
            MUSIC_JOB_UPDATE,
            json.dumps(
                MusicJobUpdateResponse(id=music_job_id, status="STARTED").model_dump()
            ),
        )
        filename = await retrieve_audio_file(music_job=music_job)
        artwork_info = None
        try:
            artwork_info = await imagedownloader.retrieve_artwork(
                artwork_url=music_job.artwork_url
            )
        except Exception:
            pass
        await asyncio.to_thread(
            update_audio_tags,
            music_job=music_job,
            filename=filename,
            artwork_info=artwork_info,
        )
        new_filename = sanitize_filename(
            "{folder}/{job_id}/{title} {artist}.mp3"
        ).format(
            folder=settings.aws_s3_music_folder,
            job_id=str(music_job.id),
            title=music_job.title.lower(),
            artist=music_job.artist.lower(),
        )

        async with aiofiles.open(filename, mode="rb") as f:
            await s3.upload_file(
                filename=new_filename, body=await f.read(), content_type="audio/mpeg"
            )

        await redis.publish(
            MUSIC_JOB_UPDATE,
            json.dumps(
                MusicJobUpdateResponse(id=music_job_id, status="COMPLETED").model_dump()
            ),
        )


async def on_failed_music_job(ctx: SAQContext):
    job = ctx["job"]
    session = ctx["db_sessionmaker"]()
    if job.function == run_music_job.__qualname__:
        music_job_id = job.kwargs.get("music_job_id")
        music_jobs_repo = MusicJobRespository(session=session)
        music_job = await music_jobs_repo.get_one(MusicJob.id == music_job_id)
        music_job.failed = True
        await music_jobs_repo.update(music_job)


tasks = [run_music_job]
on_fail_tasks = {run_music_job.__qualname__: on_failed_music_job}
