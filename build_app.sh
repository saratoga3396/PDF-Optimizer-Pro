#!/bin/bash

# Directory setup
APP_NAME="PDF自動処理"
APP_PATH="./${APP_NAME}.app"

# Create the AppleScript source
cat <<EOF > build_droplet.applescript
on open inputFiles
    -- Get the absolute path to the folder containing this app
    set appPath to POSIX path of (path to me)
    -- Remove trailing slash if present for dirname
    if appPath ends with "/" then set appPath to text 1 thru -2 of appPath
    set appDir to do shell script "dirname " & quoted form of appPath
    
    -- Define paths
    set venvPython to appDir & "/venv/bin/python3"
    set mainScript to appDir & "/main.py"
    
    -- Loop through dropped files
    repeat with aFile in inputFiles
        set filePath to POSIX path of aFile
        
        -- Build command
        set cmd to quoted form of venvPython & " " & quoted form of mainScript & " " & quoted form of filePath
        
        try
            -- Execute command
            do shell script cmd
        on error errMsg
            display dialog "処理中にエラーが発生しました:\n" & errMsg buttons {"OK"} icon stop
        end try
    end repeat
    
    display notification "ファイルの処理が完了しました" with title "PDF便利ツール" sound name "Glass"
end open

on run
    display dialog "このアイコンにPDFファイルをドラッグ＆ドロップしてください。" buttons {"OK"} default button "OK"
end run
EOF

# Compile the AppleScript into an Application
echo "Building ${APP_NAME}.app..."
osacompile -o "$APP_PATH" build_droplet.applescript

# Clean up source
rm build_droplet.applescript

echo "Done. Created ${APP_PATH}"
echo "You can now drag and drop files onto this icon."
