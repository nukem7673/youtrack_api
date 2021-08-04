# Basic Run


# 1. Set environment variables
    YT_API_TOKEN (see: https://www.jetbrains.com/help/youtrack/standalone/Manage-Permanent-Token.html)
        ex: export YT_API_TOKEN=<your_api_token>
    YT_PROJECT (your youtrack project, this is what prepends your issue numbers in YouTrack)
        ex: export YT_PROJECT=ESW

# 2. Install required python libraries
    pip3 install aiohttp asyncio

# 3. Run the project from root dir using the following command
    python3 __init__.py    

# 4. Output:
    - ./attachments/ : 
        - Where downloaded attachments end up
        - File names have random strings appended if another file exists already with the same name

    - ./attachment_issue_map :
        - Stores a mapping of downloaded filenames with the issue_id they were associated with