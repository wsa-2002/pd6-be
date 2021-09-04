import codecs
import csv
import io
import typing
from typing import Sequence, Tuple

from base import enum
import exceptions as exc
import persistence.database as db
import persistence.s3 as s3

from base import do

TEAM_TEMPLATE = b'Label,TeamName,TeamMember,Role'
TEAM_TEMPLATE_FILENAME = 'team_template.csv'

add = db.team.add
edit = db.team.edit
browse = db.team.browse
read = db.team.read
delete = db.team.delete

add_member = db.team.add_member
edit_member = db.team.edit_member
browse_members = db.team.browse_members
delete_member = db.team.delete_member


async def get_template_file() -> tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(TEAM_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, TEAM_TEMPLATE_FILENAME


async def import_team(team_file: typing.IO, class_id: int):
    try:
        rows = csv.DictReader(codecs.iterdecode(team_file, 'utf_8_sig'))
        for row in rows:
            await db.team.add_team_and_add_member(team_name=row['TeamName'], class_id=class_id, team_label=row['Label'],
                                                  account_referral=row['TeamMember'], role=enum.RoleType(row['Role']))
    except:
        raise exc.IllegalInput
