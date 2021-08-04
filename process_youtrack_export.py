import json


def pull_required_data_from_issue(issue):
    '''The api returns a lot more data than we need to actually write into the csv. Filter out unnecessary items and return new issue object'''
    
    toExport = {
        "Summary": issue["summary"],
        "Description": issue["description"],
        "Issue ID": issue["id"]
    }


    requiredCustomFields = [
        "Type",
        "State",
        "Priority",
        "Assignee"
    ]

    customFields = list(filter(lambda customField: customField["projectCustomField"]["field"]["name"] in requiredCustomFields, issue["customFields"]))
    # TODO: Stop filtering any data and just add the new fields to an dict
        # THEN use keys as the header for csv file
    for field in customFields:
        if not field["value"]:
            continue
        # shorthand
        field_name = field["projectCustomField"]["field"]["name"]

        
        # mapping values
        toExport[field_name] = field["value"]["name"].replace("\"", "'").replace('ž', 'z').replace(",", "").strip()

    # Fill in missing data
    for field in requiredCustomFields:
        if field not in toExport:
            toExport[field] = " "

    
    # One last format to ensure all special characters are removed
    for field in toExport:
        if not toExport[field]:
            toExport[field] = " "

        if toExport[field] is not " ":
            sanitizedField = toExport[field].replace("'", "").replace("\"", "").replace("`", "").strip()

            if sanitizedField is not field:
                print(f'for key {field}\noldString: {toExport[field]}')
                print(f'newString: {sanitizedField}')
                toExport[field] = sanitizedField
            
    # print(json.dumps(toExport))
    return toExport

    
def export_to_csv(youtrack_json):
    # Export to csv
    with open("./youtrack_export.csv", "w") as f:
        f.write("Issue ID,Summary,Issue Type,State,Description,Priority,Assignee\n")
        for issue in youtrack_json:
            issue_data = pull_required_data_from_issue(issue)
            f.write(f'{issue_data["Issue ID"]},"{issue_data["Summary"]}","{issue_data["State"]},"{issue_data["Type"]}","{issue_data["Description"]}","{issue_data["Priority"]}","{issue_data["Assignee"]}"\n')


def write_to_json(youtrack_json):
    with open("./youtrack_data.json", "w") as f:
        json.dump(youtrack_json, f)
