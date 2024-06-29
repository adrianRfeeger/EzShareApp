import pathlib
import requests
import datetime
import bs4
import urllib.parse
import re
import os
import logging
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

def recursive_traversal(ezshare, url, dir_path, total_files, processed_files):
    files, dirs = list_dir(ezshare, url)
    processed_files = check_files(ezshare, files, url, dir_path, total_files, processed_files)
    processed_files = check_dirs(ezshare, dirs, url, dir_path, total_files, processed_files)
    return processed_files

def list_dir(ezshare, url):
    html_content = requests.get(url, timeout=5)
    soup = bs4.BeautifulSoup(html_content.text, 'html.parser')
    files = []
    dirs = []

    pre_text = soup.find('pre').decode_contents()
    lines = pre_text.split('\n')

    for line in lines:
        if line.strip():  # Skip empty line
            parts = line.rsplit(maxsplit=2)
            modifypart = parts[0].replace('- ', '-0').replace(': ', ':0')
            regex_pattern = r'\d*-\d*-\d*\s*\d*:\d*:\d*'

            match = re.search(regex_pattern, modifypart)

            if match:
                file_ts = datetime.datetime.strptime(match.group(),
                                                     '%Y-%m-%d   %H:%M:%S').timestamp()
            else:
                file_ts = 0

            soupline = bs4.BeautifulSoup(line, 'html.parser')
            link = soupline.a
            if link:
                link_text = link.get_text(strip=True)
                # Oscar expects STR.edf, not STR.EDF
                if link_text == 'STR.EDF':
                    link_text = 'STR.edf'

                link_href = link['href']

                if link_text in ezshare.ignore or link_text.startswith('.'):
                    continue
                parsed_url = urllib.parse.urlparse(link_href)
                if parsed_url.path.endswith('download'):
                    files.append((link_text, parsed_url.query, file_ts))
                elif parsed_url.path.endswith('dir'):
                    dirs.append((link_text, link_href))
    return files, dirs

def check_files(ezshare, files, url, dir_path: pathlib.Path, total_files, processed_files):
    for filename, file_url, file_ts in files:
        local_path = dir_path / filename
        absolute_file_url = urllib.parse.urljoin(url, f'download?{file_url}')
        if total_files == 0:
            ezshare.update_status(f'Downloading file "{filename}" {processed_files + 1}/{total_files} (0%)')
        else:
            ezshare.update_status(f'Downloading file "{filename}" {processed_files + 1}/{total_files} ({int((processed_files + 1) / total_files * 100)}%)')
        downloaded = download_file(ezshare, absolute_file_url, local_path, file_ts=file_ts)
        if downloaded:
            processed_files += 1
            ezshare.update_progress(0 if total_files == 0 else int(processed_files / total_files * 100))
    return processed_files

def download_file(ezshare, url, file_path: pathlib.Path, file_ts=None):
    mtime = 0
    already_exists = file_path.is_file()
    if already_exists:
        mtime = file_path.stat().st_mtime
    if (ezshare.overwrite or mtime < file_ts) and not (already_exists and ezshare.keep_old):
        logger.debug('Downloading %s from %s', str(file_path), url)
        response = ezshare.session.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        if total_size == 0:
            logger.warning('File %s has zero total size, skipping progress update.', str(file_path))
            with file_path.open('wb') as fp:
                pass  # Create an empty file if it does not exist
        else:
            with NamedTemporaryFile(delete=False, dir=file_path.parent) as tmp_file:
                tmp_file_path = pathlib.Path(tmp_file.name)
                try:
                    for data in response.iter_content(block_size):
                        tmp_file.write(data)

                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())

                    tmp_file_path.replace(file_path)
                    logger.info('%s written', str(file_path))

                    if file_ts:
                        os.utime(file_path, (file_ts, file_ts))
                except Exception as e:
                    tmp_file_path.unlink(missing_ok=True)
                    logger.error('Error downloading file %s: %s', str(file_path), str(e))
                    return False

        return True
    else:
        logger.info('File %s already exists and has not been updated. Skipping because overwrite is off.',
                    str(file_path))
        return False

def check_dirs(ezshare, dirs, url, dir_path: pathlib.Path, total_files, processed_files):
    for dirname, dir_url in dirs:
        new_dir_path = dir_path / dirname
        new_dir_path.mkdir(exist_ok=True)
        absolute_dir_url = urllib.parse.urljoin(url, dir_url)
        processed_files = recursive_traversal(ezshare, absolute_dir_url, new_dir_path, total_files, processed_files)
    return processed_files
