import persistence.database as db


add = db.class_.add
edit = db.class_.edit
browse = db.class_.browse
read = db.class_.read
delete = db.class_.delete_cascade

add_members = db.class_.add_members
add_members_by_account_referral = db.class_.add_members_by_account_referral
edit_member = db.class_.edit_member
browse_member_emails = db.class_.browse_member_emails
browse_member_account_with_student_card_and_institute = db.class_vo.browse_member_account_with_student_card_and_institute
browse_class_member_with_account_id = db.class_vo.browse_class_member_with_account_id
browse_class_member_with_account_referral = db.class_vo.browse_class_member_with_account_referral

delete_member = db.class_.delete_member
delete_all_members_in_class = db.class_.delete_all_members_in_class
