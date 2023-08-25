import codecs
import csv
import io
import typing
from datetime import datetime

from base import do, enum
import exceptions as exc
import persistence.database as db
import persistence.s3 as s3
import util

ACCOUNT_TEMPLATE = b'RealName,Username,Password,AlternativeEmail,Nickname'
ACCOUNT_TEMPLATE_FILENAME = 'account_template.csv'


async def get_account_template() -> tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(ACCOUNT_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, ACCOUNT_TEMPLATE_FILENAME


async def import_account(account_file: typing.IO):
    try:
        standard_headers = ACCOUNT_TEMPLATE.decode('utf_8_sig').split(',')
        rows = csv.DictReader(codecs.iterdecode(account_file, 'utf_8_sig'))
        data = []

        if set(rows.fieldnames) != set(standard_headers):
            raise exc.IllegalInput

        for row in rows:
            for header in standard_headers:
                if header != 'AlternativeEmail' and row[header] == "":
                    raise exc.IllegalInput
            data.append((row['RealName'], row['Username'], util.security.hash_password(row['Password']),
                         row['AlternativeEmail'], row['Nickname']))
        await db.account.batch_add_normal(data)
    except UnicodeDecodeError:
        raise exc.FileDecodeError


TEAM_TEMPLATE = b'TeamName,Manager,Member 2,Member 3,Member 4,Member 5,Member 6,Member 7,Member 8,Member 9,Member 10'
TEAM_TEMPLATE_FILENAME = 'team_template.csv'


async def get_team_template() -> tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(TEAM_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, TEAM_TEMPLATE_FILENAME


async def import_team(team_file: typing.IO, class_id: int, label: str):
    try:
        standard_headers = TEAM_TEMPLATE.decode('utf_8_sig').split(',')
        rows = csv.DictReader(codecs.iterdecode(team_file, 'utf_8_sig'))
        data = []

        if set(rows.fieldnames) != set(standard_headers):
            raise exc.IllegalInput

        for row in rows:
            member_roles = []
            for column_name, item in row.items():
                if column_name == 'TeamName':  # column name is 'TeamName'
                    continue
                if column_name == 'Manager' and item:  # column name is 'Manager'
                    member_roles += [(item, enum.RoleType.manager)]
                elif item:
                    member_roles += [(item, enum.RoleType.normal)]
            data.append((row['TeamName'], member_roles))
        await db.team.add_team_and_add_member(class_id=class_id, team_label=label, datas=data)
    except UnicodeDecodeError:
        raise exc.FileDecodeError


GRADE_TEMPLATE = b'Receiver,Score,Comment,Grader\nB05705088,10,"here for comment",B99705006'
GRADE_TEMPLATE_FILENAME = 'grade_template.csv'


async def import_class_grade(grade_file: typing.IO, title: str, class_id: int, update_time: datetime):
    try:
        standard_headers = GRADE_TEMPLATE.decode('utf_8_sig').split('\n')[0].split(',')
        rows = csv.DictReader(codecs.iterdecode(grade_file, 'utf_8_sig'))
        data = []

        if set(rows.fieldnames) != set(standard_headers):
            raise exc.IllegalInput

        for row in rows:
            data.append((row['Receiver'], row['Score'], row['Comment'], row['Grader']))
        await db.grade.batch_add(class_id=class_id, title=title, grades=data, update_time=update_time)
    except UnicodeDecodeError:
        raise exc.FileDecodeError


async def get_grade_template() -> tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(GRADE_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, GRADE_TEMPLATE_FILENAME
