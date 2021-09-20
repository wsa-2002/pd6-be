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

TEAM_TEMPLATE = b'TeamName,Manager,Member 2,Member 3,Member 4,Member 5,Member 6,Member 7,Member 8,Member 9,Member 10'
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


async def import_team(team_file: typing.IO, class_id: int, label: str):
    try:
        rows = csv.DictReader(codecs.iterdecode(team_file, 'utf_8_sig'))
        for row in rows:
            member_roles = []
            for item in row:
                if str(item) == 'TeamName':  # column name is 'TeamName'
                    continue
                if str(item) == 'Manager':  # column name is 'Manager'
                    member_roles += [(row[str(item)], enum.RoleType.manager)]
                elif row[str(item)]:
                    member_roles += [(row[str(item)], enum.RoleType.normal)]

            await db.team.add_team_and_add_member(team_name=row['TeamName'], class_id=class_id,
                                                  team_label=label, member_roles=member_roles)
    except UnicodeDecodeError:
        raise exc.FileDecodeError
    except:
        raise exc.IllegalInput


async def add_members(team_id: int, member_roles: Sequence[Tuple[str, enum.RoleType]]) -> Sequence[int]:
    try:
        return await db.team.add_members(team_id=team_id, member_roles=member_roles)
    except:
        raise exc.IllegalInput




