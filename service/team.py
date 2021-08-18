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

add_members_by_account_referral = db.team.add_members_by_account_referral
delete_all_members_in_team = db.team.delete_all_members_in_team
