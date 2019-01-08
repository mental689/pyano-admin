from django.test import TestCase

# Create your tests here.

from vatic.video import *
from search.youtube import download_youtube_video
from django.conf import settings


class VideoTestCase(TestCase):
    def setUp(self):
        pass

    def test_video_downloader(self):
        output_dir = '{}/static/videos'.format(settings.BASE_DIR)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        download_youtube_video(youtube_ids=['fs-ifFsc8Bg'], output_folder=output_dir)

    def test_video_extractor(self):
        test_extract()
        self.assertTrue(os.path.exists('{}/static/frames/fs-ifFsc8Bg'.format(settings.BASE_DIR)))

    def test_video_loader(self):
        test_load()
