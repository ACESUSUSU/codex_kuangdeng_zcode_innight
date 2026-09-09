-- Only use when the user has explicitly authorized AppleScript control of ZCode.
-- Focus the intended chat composer first. Fill and send are deliberately separate.
on run argv
    if (count of argv) < 1 then error "Expected fill <prompt-file> or send"
    set actionName to item 1 of argv
    if actionName is "fill" then
        if (count of argv) is not 2 then error "Expected fill <prompt-file>"
        set dispatchText to read POSIX file (item 2 of argv) as «class utf8»
        set savedClipboard to the clipboard
        try
            tell application id "dev.zcode.app" to activate
            delay 0.3
            tell application "System Events"
                tell process "ZCode"
                    set frontmost to true
                    keystroke "a" using command down
                end tell
            end tell
            set the clipboard to dispatchText
            tell application "System Events" to tell process "ZCode" to keystroke "v" using command down
            delay 0.7
            set the clipboard to savedClipboard
            return "FILLED_NOT_SENT"
        on error errMsg number errNum
            set the clipboard to savedClipboard
            error errMsg number errNum
        end try
    else if actionName is "send" then
        tell application id "dev.zcode.app" to activate
        delay 0.2
        tell application "System Events" to tell process "ZCode" to key code 36
        return "SEND_KEY_PRESSED_ONCE"
    else
        error "Only fill and send are supported"
    end if
end run
