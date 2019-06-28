from img_downloader.img_downloader import ImageDownloader


def callback(block_num, read_size, total_size):
    print('{} | {} | {}'.format(block_num, read_size, total_size))


d = ImageDownloader(
    'https://provo-mirror.opensuse.org/repositories/Cloud:/Images:/Leap_15.0/images/',
    'openSUSE-Leap-15.0-GCE',
    'gce',
    version_format='{kiwi_version}-Build{obs_build}',
    download_directory='/run/media/smarlow/DellHDD/mash/images',
    #report_callback=callback
)

d.get_image()
