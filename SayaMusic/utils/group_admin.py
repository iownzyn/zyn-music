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


async def can_control_playback(client, group_id: int, user_id: int, action: str = "") -> bool:
    """Allow actual group admins always; group members only when group mode is on.
    Stopping/ending a stream is always reserved for real group admins.
    """
    if await is_real_group_admin(client, group_id, user_id):
        return True
    if action.lower() in {"stop", "end"}:
        return False
    from SayaMusic.utils.database import is_group_control_mode
    return await is_group_control_mode(group_id)
