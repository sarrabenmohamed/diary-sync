import subprocess


def move_to_photos_trash(uuid: str) -> bool:
    """
    Move a Photos asset to the Photos trash by UUID via AppleScript.
    Returns True on success, False otherwise.
    """
    script = f"""
    tell application "Photos"
        set theItems to (every media item whose id is "{uuid}")
        if length of theItems > 0 then
            delete (item 1 of theItems)
            return "OK"
        else
            return "NOT_FOUND"
        end if
    end tell
    """
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "OK" in result.stdout
