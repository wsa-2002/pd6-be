from base.enum import Role

from .base import SafeExecutor


async def get_system_role_by_account_id(account_id: int, disabled_as_guest=True) -> Role:
    async with SafeExecutor(
            event='get system role by account id',
            sql=r'SELECT account.is_enabled, role.id'
                r'  FROM account, role'
                r' WHERE account.id = %(account_id)s'
                r'   AND account.role_id = role.id',
            account_id=account_id,
            fetch=1,
    ) as (is_enabled, role_id):
        return Role(role_id) if is_enabled or not disabled_as_guest else Role.guest
