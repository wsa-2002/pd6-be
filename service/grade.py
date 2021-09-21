import csv
import codecs
import datetime
import io
from typing import Tuple
import typing

import persistence.database as db
import persistence.s3 as s3
import exceptions as exc

from base import do


GRADE_TEMPLATE = b'Receiver,Score,Comment,Grader\nB05705088,10,"here for comment",B99705006'
GRADE_TEMPLATE_FILENAME = 'grade_template.csv'


add = db.grade.add
edit = db.grade.edit
browse = db.grade.browse
read = db.grade.read
delete = db.grade.delete


async def import_class_grade(grade_file: typing.IO, title: str, class_id: int, update_time: datetime):
    try:
        rows = csv.DictReader(codecs.iterdecode(grade_file, 'utf_8_sig'))
        data = []
        for row in rows:
            data.append((row['Receiver'], row['Score'], row['Comment'], row['Grader']))
        await db.grade.batch_add(class_id=class_id, title=title, grades=data, update_time=update_time)
    except UnicodeDecodeError:
        raise exc.FileDecodeError
    except:
        raise exc.IllegalInput


async def get_template_file() -> Tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(GRADE_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, GRADE_TEMPLATE_FILENAME
