from os import path, environ
from aiohttp.streams import StreamReader
import requests
import json
import asyncio
import aiohttp
import random
import string


# URL vars
YT_API_TOKEN = environ.get('YT_API_TOKEN')

# Check variables are set
if not YT_API_TOKEN:
    print(f"Environment variable: YT_API_TOKEN is required. Please set and rerun script.")
    exit()


# GLOBALS
base = "https://churchillnavigation.myjetbrains.com/youtrack/api/"
headers = {
    "Authorization": f"Bearer {YT_API_TOKEN}",
    "Accept": "application/json",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}


def get_youtrack_data(project, log=True, debug=True):
    # Set base url for api - allows modularity
    # TODO: set to flag later
    endpoint = "issues?"
    query = f"query=project:{project}"
    return_fields = "fields=idReadable,summary,id,description,url,customFields($type,id,projectCustomField($type,id,field($type,id,name)),value($type,avatarUrl,buildLink,color(id),fullName,id,isResolved,localizedName,login,minutes,name,presentation,text))"
    # return_fields = "fields=idReadable,summary,description,customFields(projectCustomFields(value)"

    url = base + endpoint + query + "&" + return_fields

    r = requests.get(url=url, headers=headers)

    parsed = json.loads(r.text)

    if debug:
        print(r.text)

    if log:
        issue_ids = [issue['id'] for issue in parsed]

        with open("./log.csv", "w") as f:
            f.write(json.dumps(extract_issue_ids(issue_ids)))

    return parsed


def extract_issue_ids(issues):
    return [issue['id'] for issue in issues]


# Setup async GET requests
async def get(session, request_url, issue_id):
    '''  Generates a coroutine get request given supplied params, which can be gathered and 
    sent simultaneously using asyncio.gather()  '''

    # Using a passed session and given info, generate the GET request
    async with session.get(
        request_url,
        headers=headers,
    ) as response:
        # Parse json from response
        r_json = await response.json()
        print(f"ran {issue_id}.\n{r_json}")
        if (len(r_json)):  # will return empty array if no attachment is found
            print(f"Attachment found for {issue_id}.\n{r_json[0]['url']}")
            return (issue_id, r_json[0]['url'])


# async GET urls loop
async def get_youtrack_attachment_urls(issue_ids):
    '''
    Pull YouTrack Issue Attachments from YouTrack API using co-routines

    Parses, formats, and writes data to text file in tuple() 
    '''
    async with aiohttp.ClientSession() as session:
        # create queue
        post_tasks = []
        # prepare coroutines
        for issue_id in issue_ids:
            endpoint = f"https://churchillnavigation.myjetbrains.com/youtrack/api/issues/{issue_id}/attachments?fields=name,size,mimeType,extension,charset,url"
            post_tasks.append(get(session, endpoint, issue_id))
        # execute them all simultaneously
        resp = await asyncio.gather(*post_tasks)

        with open('attachment_urls_and_issue_ids.json', 'w') as f:
            f.write(json.dumps(resp))

        return resp


# MAIN for attachment urls
def get_all_attachments(issue_ids=None):
    if (issue_ids == None):
        # If an id list isn't passed, we can generate one from the stored data
        issue_ids = []
        with open('youtrack_data.json', 'r') as f:
            issues = json.loads(f.read())
            issue_ids = [issue['id'] for issue in issues]

    if (issue_ids == None):
        # If that also fails, i.e. no data is stored, exit
        return

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_youtrack_attachment_urls(issue_ids))
    loop.close()


# Download all attachments given a map with (issue_id, attachment_url)
async def download_all_attachments(attachment_issueID_map):
    ''''Store file location with issue_id to be reconstructed later'''
    asyncio_semaphore = asyncio.Semaphore(50)

    async with aiohttp.ClientSession() as session:
        # Container for download tasks
        get_tasks = []

        for issue_id, attachment_url in attachment_issueID_map:
            print(f'issue_id:{issue_id} |||| url: {attachment_url}')
            get_tasks.append(get_attachment(session, attachment_url, issue_id, asyncio_semaphore))

        resp = await asyncio.gather(*get_tasks)
        return resp


# Perform download
async def get_attachment(session, url, issue_id, asyncio_semaphore):
    ''''GET request to url, store file, save filename/location with issue_id'''
    full_url = "https://churchillnavigation.myjetbrains.com" + url
    async with asyncio_semaphore:
        async with session.get(full_url, headers=headers) as response:
            img = response.content
            if not isinstance(img, StreamReader):
                print('not a bytes object . . . skipping')
                print(img)
                return None

            # Get filename from response's content-disposition
            content_disposition = response.headers.get('content-disposition')
            fname = get_filename_from_content_disposition(content_disposition)
            # Define storage path in 'attachments'
            f_path = f'./attachments/{fname}'

            # Check if a file already exists, if so, append a random string
            if path.isfile(f_path):
                print(f"{fname} exisits. Rewriting . . . ")
                random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                (file_name, extension) = path.splitext(fname)
                f_path = f'./attachments/{file_name}_{random_string}.{extension}'

            # Save attachment
            with open(f_path, 'wb') as f:
                f.write(await response.content.read())
                print(f"completed writing {f_path}")

            # Store attachment location with it's issue_id
            with open('attachment_issue_map', 'a') as f:
                # map in a tuple
                a_to_issue_map = (issue_id, f_path)
                f.write(json.dumps(a_to_issue_map))


# Helper to grab filename from the response
def get_filename_from_content_disposition(cd):
    '''Extracts filename from content-disposition'''
    if not cd:
        return None
    fname = cd[cd.index("\""):]
    print(fname)
    fname = fname.replace("\"", "")
    print(fname)
    if len(fname) == 0:
        return None

    return fname


# Download Loop
def download_main(attachment_urls_and_issue_ids):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(download_all_attachments(attachment_urls_and_issue_ids))
    asyncio.run(download_all_attachments(attachment_urls_and_issue_ids))
