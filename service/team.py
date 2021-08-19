from typing import Sequence, Tuple

from base import enum
import persistence.database as db


add = db.team.add
edit = db.team.edit
browse = db.team.browse
read = db.team.read
delete = db.team.delete

add_member = db.team.add_member
edit_member = db.team.edit_member
browse_members = db.team.browse_members
delete_member = db.team.delete_member


async def replace_members(team_id: int, member_roles: Sequence[Tuple[str, enum.RoleType]]) -> None:
    await db.team.delete_all_members_in_team(team_id=team_id)
    await db.team.add_members_by_account_referral(team_id=team_id,
                                                  member_roles=[(account_referral, role)
                                                                for (account_referral, role) in member_roles])
