import asyncio
from dataclasses import dataclass
import os
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import log
from .. import http_client


@dataclass
class MossOptions:

    submission_files: dict[str, bytes]

    """
    The -l option specifies the source language of the tested programs.
    Moss supports many different languages; see the variable "languages" below for the
    full list.
    """
    language: str

    """
    The -d option specifies that submissions are by directory, not by file.
    That is, files in a directory are taken to be part of the same program,
    and reported matches are organized accordingly by directory.
    """
    directory_mode: bool

    """
    The -b option names a "base file".  Moss normally reports all code
    that matches in pairs of files.  When a base file is supplied,
    program code that also appears in the base file is not counted in matches.
    A typical base file will include, for example, the instructor-supplied
    code for an assignment.  Multiple -b options are allowed.  You should
    use a base file if it is convenient; base files improve results, but
    are not usually necessary for obtaining useful information.
    """
    base_files: dict[str, bytes]

    """
    The -m option sets the maximum number of times a given passage may appear
    before it is ignored.  A passage of code that appears in many programs
    is probably legitimate sharing and not the result of plagiarism.  With -m N,
    any passage appearing in more than N programs is treated as if it appeared in
    a base file (i.e., it is never reported).  Option -m can be used to control
    moss' sensitivity.  With -m 2, moss reports only passages that appear
    in exactly two programs.  If one expects many very similar solutions
    (e.g., the short first assignments typical of introductory programming
    courses) then using -m 3 or -m 4 is a good way to eliminate all but
    truly unusual matches between programs while still being able to detect
    3-way or 4-way plagiarism.  With -m 1000000 (or any very
    large number), moss reports all matches, no matter how often they appear.
    The -m setting is most useful for large assignments where one also a base file
    expected to hold all legitimately shared code.  The default for -m is 10.
    """
    ignore_threshold: int

    """
    The -c option supplies a comment string that is attached to the generated
    report.  This option facilitates matching queries submitted with replies
    received, especially when several queries are submitted at once.
    :return:
    """
    subtitle: str

    """
    The -n option determines the number of matching files to show in the results.
    The default is 250.
    """
    max_results: int

    """
    The -x option sends queries to the current experimental version of the server.
    The experimental server has the most recent Moss features and is also usually
    less stable (read: may have more bugs).
    """
    use_experimental: bool = False

    host: str = 'moss.stanford.edu'
    port: int = 7690
    user_id: int = 639745875


async def submit_report(opt: MossOptions) -> str:
    log.info(f"Connecting to moss server {opt.host=} {opt.port=}")
    reader, writer = await asyncio.open_connection(opt.host, port=opt.port)

    for message in (
        f'moss {opt.user_id}\n',
        f'directory {1 * opt.directory_mode}\n',
        f'X {1 * opt.use_experimental}\n',
        f'maxmatches {opt.ignore_threshold}\n',
        f'show {opt.max_results}\n',
    ):
        log.info(f'Sending to moss, {message=}')
        writer.write(message.encode())

    writer.write(f'language {opt.language}\n'.encode())
    response = await reader.read(1024)
    log.info(f'Language {opt.language=} response from moss: {response.decode()}')
    if response.decode().strip() == 'no' or response.decode().strip() != 'yes':
        raise RuntimeError  # todo

    for filename, file in opt.base_files.items():
        writer.write(f'file {0} {opt.language} {len(file)} {filename}\n'.encode())
        writer.write(file)

    for i, (filename, file) in enumerate(opt.submission_files.items(), start=1):
        writer.write(f'file {i} {opt.language} {len(file)} {filename}\n'.encode())
        writer.write(file)

    injected_title = f'</p><h1>{opt.subtitle}</h1><p>'
    writer.write(f'query 0 {injected_title}\n'.encode())

    response = await reader.read(1024)

    writer.write('end\n'.encode())

    writer.close()
    await writer.wait_closed()

    return response.decode().strip().replace('\n', '')


def parse(base_url, page: bytes, sub_folder: str) -> tuple[bytes, dict[str, str]]:
    soup = BeautifulSoup(page.decode(), 'lxml')

    extracted_urls = {}
    for link_html_obj in soup.find_all(['a', 'frame']):
        if link_html_obj.has_attr('href'):
            link = link_html_obj.get('href')
        else:
            link = link_html_obj.get('src')

        # Download only results urls
        if not link or 'match' not in link:
            continue

        if '#' in link:
            link, bookmark = link.split('#')
            bookmark = '#' + bookmark
        else:
            link, bookmark = link, ''

        basename = os.path.basename(link)

        if basename == link:  # Handling relative urls
            link = urljoin(base_url, link)

        if sub_folder:
            basename = os.path.join(sub_folder, basename)

        if link_html_obj.name == "a":
            link_html_obj['href'] = basename + bookmark
        elif link_html_obj.name == "frame":
            link_html_obj['src'] = basename

        extracted_urls[basename] = link

    return soup.encode(), extracted_urls


async def download_report(index_url: str, sub_folder: str) -> tuple[bytes, dict[str, bytes]]:
    index = await http_client.download(index_url)

    parsed_index, extracted_urls = parse(index_url, index, sub_folder)
    match_files = {
        rel_url: downloaded
        for rel_url, downloaded
        in zip(extracted_urls, await http_client.batch_download(*extracted_urls.values()))
    }

    match_inner_files = {}
    for match_file_url, file in match_files.items():
        parsed_file, other_extracted_urls = parse(index_url, file, sub_folder='')
        match_files[match_file_url] = parsed_file
        match_inner_files |= {
            os.path.join(sub_folder, rel_url): downloaded
            for rel_url, downloaded
            in zip(other_extracted_urls, await http_client.batch_download(*other_extracted_urls.values()))
            if rel_url not in match_files and rel_url not in match_inner_files
        }

    return parsed_index, match_files | match_inner_files
