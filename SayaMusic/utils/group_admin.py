from pyrogram.enums import ChatMemberStatus


async def is_real_group_admin(client, chat_id: int, user_id: int) -> bool:
    """Return True only for a current administrator/owner of this exact group."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    )
