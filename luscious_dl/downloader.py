﻿import multiprocessing as mp
import os
import time
from itertools import repeat

import requests

from luscious_dl.logger import logger
from luscious_dl.utils import create_folder


class Downloader:
  """Downloader class."""
  def __init__(self, output_dir: str, threads: int = 1, retries: int = 5, timeout: int = 30, delay: int = 0,
               foldername_format: str = '%t') -> None:
    self.output_dir = output_dir
    self.threads = threads
    self.retries = retries
    self.timeout = timeout
    self.delay = delay
    self.foldername_format = foldername_format

  def download_picture(self, picture_url: str, album_folder: str) -> None:
    """
    Download picture.
    :param picture_url: picture url
    :param album_folder: album folder path
    """
    try:
      if picture_url.startswith('//'):
        picture_url = picture_url.replace('//', '', 1)
      if not picture_url.startswith('http://') and not picture_url.startswith('https://'):
        picture_url = f'https://{picture_url}'
      picture_name = picture_url.rsplit('/', 1)[1]
      picture_path = os.path.join(album_folder, picture_name)
      if not os.path.exists(picture_path):
        logger.info(f'Start downloading: {picture_url}')
        retry = 1
        response = requests.get(picture_url, stream=True, timeout=self.timeout)
        while response.status_code != 200 and retry <= self.retries:
          logger.warning(f'{retry}º Retry: {picture_name}')
          response = requests.get(picture_url, stream=True, timeout=self.timeout)
          retry += 1
        if retry > self.retries:
          raise Exception('Reached maximum number of retries')
        if len(response.content) > 0:
          with open(picture_path, 'wb') as image:
            image.write(response.content)
            logger.log(5, f'Completed download of: {picture_name}')
        else:
          raise Exception('Zero content')
      else:
        logger.warning(f'Picture already exists: {picture_name} ')
    except Exception as e:
      logger.error(f'Failed to download picture: {picture_url}\n{e}')

  def download(self, urls: list[str], folder_name: str) -> None:
    """
    Start download process.
    :param urls: list of image URLs
    :param folder_name: album folder name
    """
    start_time = time.time()

    album_folder = os.path.join(self.output_dir, folder_name)
    create_folder(album_folder)

    pool = mp.Pool(self.threads)
    pool.starmap(self.download_picture, zip(urls, repeat(album_folder)))

    end_time = time.time()
    logger.info(f'Finished in {time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))}')

    if self.delay:
      time.sleep(self.delay)
