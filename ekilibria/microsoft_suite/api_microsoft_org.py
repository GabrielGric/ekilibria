import asyncio
import os
from utils import build_windows_to_iana_map
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from azure.core.credentials import AccessToken
from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions
from msgraph.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder
from msgraph.generated.users.item.events.events_request_builder import EventsRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.headers_collection import HeadersCollection
from msgraph import GraphServiceClient

# Link for concent to access Microsoft Graph API:
# https://login.microsoftonline.com/common/adminconsent?client_id=845ac38e-8122-4897-939d-0532d48feb95

CLIENT_ID_MICROSOFT = os.getenv("CLIENT_ID_MICROSOFT")

async def get_microsoft_graph_api_token(client_id = None):

    client_id = os.getenv("CLIENT_ID_MICROSOFT")


    credential = InteractiveBrowserCredential(
        client_id=client_id,
        tenant_id="common",
        enable_support_logging=True
        )

    #scopes = "User.Read"
    token = credential.get_token("https://graph.microsoft.com/.default")
    token_dict = {"token": token.token, "expires_on": token.expires_on}
    client = create_graph_client_from_token(token_dict)
    #client = GraphServiceClient(credentials=credential)
    
    # Get user email
    try:
        user = await client.me.get()
        print(f"Authenticated as: {user.display_name} ({user.mail})")
        return user, token_dict
    except Exception as e:
        print(f"❌ Error fetching user information: {e}")
        return None

def create_graph_client_from_token(token_dict):
    # token_dict debe tener al menos 'token' y 'expires_on'
    class SimpleCredential:
        def get_token(self, *scopes, **kwargs):
            return AccessToken(token_dict['token'], token_dict['expires_on'])
    return GraphServiceClient(credentials=SimpleCredential())

# Get the user's working hours and time zone
async def user(client):

    # Get the user's profile
    user = await client.me.mailbox_settings.get()

    working_hours = user.working_hours
    working_hours_res = {
        'daysOfWeek': working_hours.days_of_week if working_hours.days_of_week else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        'startTime': working_hours.start_time if working_hours.start_time else '09:00:00',
        'endTime': working_hours.end_time if working_hours.end_time else '17:00:00',
        'timeZone': working_hours.time_zone if working_hours.time_zone else 'UTC'
    }
    return working_hours_res

# Get emails from the user's mailbox for a specific date range
async def get_mails(client, user_time_zone,iana_time_zone,from_date, to_date, folder="Inbox"):

    # Format dates to ISO 8601 with Z (UTC)
    from_date_fotmated = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_date_fotmated = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        filter=f"receivedDateTime ge {from_date_fotmated} and receivedDateTime le {to_date_fotmated}",
        orderby=["receivedDateTime desc"]
    )

    request_configuration = RequestConfiguration(
        query_parameters = query_params,
    )

    messages_response = await client.me.mail_folders.by_mail_folder_id(folder).messages.get(request_configuration=request_configuration)

    # Set default value for working_hours
    total_emails = len(messages_response.value)
    working_hours_count = 0

    for message in messages_response.value:
        received_time = message.received_date_time
        if received_time:
            # Convert received time to user's time zone
            local_received_time = received_time.astimezone(ZoneInfo(iana_time_zone))
            # Check if the email was received during working hours
            if local_received_time.strftime("%A").lower() in user_time_zone["daysOfWeek"]:
                start_hour = user_time_zone["startTime"].hour
                end_hour = user_time_zone["endTime"].hour
                if start_hour <= local_received_time.hour < end_hour:
                    working_hours_count += 1

    if folder == "Inbox":
        ## Average emails received per day
        result = {
            "emails_received": total_emails/ 7,  # Assuming the week starts on Monday and ends on Sunday
        }
    else:
        result = {
            "emails_sent": working_hours_count,
            "emails_sent_out_of_hours": total_emails - working_hours_count
        }
    return result

# Get events from the user's calendar for a specific date range
async def get_events(client, user_time_zone, iana_time_zone, from_date, to_date):
    # Format dates to ISO 8601 with Z (UTC)
    from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    ## Create query parameters for the request
    # Note: The filter and orderby parameters are set to retrieve events within the specified date range
    # and order them by start date in ascending order.
    query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(
        filter=f"start/dateTime ge '{from_date_str}' and end/dateTime le '{to_date_str}'",
        orderby=["start/dateTime asc"],
        select=["subject", "start", "end", "location"]
    )

    # Set the preferred time zone for the request
    # This is necessary to ensure that the event times are returned in the user's local time zone.
    # The time zone name should match the IANA time zone format.
    headers = HeadersCollection()
    headers.add('prefer', f'outlook.timezone="{user_time_zone["timeZone"].name}"')


    request_configuration = RequestConfiguration(
        headers=headers,
        query_parameters=query_params,
    )

    # Make the request to get the user's events
    events_response = await client.me.events.get(request_configuration=request_configuration)

    if not events_response.value:
        print("No events found for the specified date range.")

    # Initialize counters for various metrics
    total_events = len(events_response.value)
    total_duration_hours = 0
    events_outside_working_hours = 0
    events_weekend = 0
    events_in_working_hours = 0
    meetings_without_breaks = 0
    overlapping_meetings = 0
    past_end_time = None  # To track the end time of the previous event

    for event in events_response.value:

        # Convert start and end times to user's time zone
        start_time = event.start.date_time
        end_time = event.end.date_time
        start_dt = datetime.fromisoformat(start_time.replace(':00.0000000', ''))
        end_dt = datetime.fromisoformat(end_time.replace(':00.0000000', ''))
        local_start_time = start_dt.astimezone(ZoneInfo(iana_time_zone))
        local_end_time = end_dt.astimezone(ZoneInfo(iana_time_zone))


        if start_time and end_time:
            # Check if the event is at least 15 apart from the previous event
            if past_end_time and start_time:
                    time_diff = local_start_time - past_end_time
                    if time_diff.total_seconds() < 0:
                        overlapping_meetings += 1
                    elif time_diff.total_seconds() <= 15 * 60:
                        meetings_without_breaks += 1

            # Calculate duration in hours
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            total_duration_hours += duration_hours

            # Check if the event is outside working hours
            day_of_week = local_start_time.strftime('%A').lower()
            if day_of_week not in user_time_zone['daysOfWeek']:
                events_weekend += 1
            elif not (user_time_zone['startTime'] <= local_end_time.time() <= user_time_zone['endTime']):
                events_outside_working_hours += 1
            else:
                events_in_working_hours += 1


        past_end_time = local_end_time

    result = {
        "num_events": events_in_working_hours,
        "num_events_outside_hours": events_outside_working_hours,
        "total_meeting_hours": total_duration_hours,
        "avg_meeting_duration" : total_duration_hours / total_events if total_events > 0 else 0,
        "meetings_weekend": events_weekend,
        "num_meetings_no_breaks": meetings_without_breaks,
        "num_overlapping_meetings": overlapping_meetings
    }

    return result

# Recursively list all files in a folder and its subfolders
async def list_all_files_in_folder(client,drive_id, folder_id="root", path=""):

    children = await client.drives.by_drive_id(drive_id).items.by_drive_item_id(folder_id).children.get()

    files = []
    for item in children.value:
        item_path = f"{path}/{item.name}" if path else item.name
        if item.folder:
            # It's a folder, recurse into it
            files += await list_all_files_in_folder(client,drive_id, item.id, item_path)
        else:
            # It's a file
            files.append(item)
    return files

# Get files from the user's OneDrive for a specific date range
async def get_files(client, user_time_zone, iana_time_zone, from_date, to_date):

    drive = await client.me.drive.get()

    files = await list_all_files_in_folder(client, drive.id)


    if not files:
        print("No files found in OneDrive.")
        return []

    total_files = 0
    created = 0
    modified = 0

    for file in files:

        created_time = file.created_date_time
        last_modified_time = file.last_modified_date_time

        ## Convert to user's timezone
        created_time = created_time.astimezone(ZoneInfo(iana_time_zone))
        last_modified_time = last_modified_time.astimezone(ZoneInfo(iana_time_zone))

        ## Count files created this week
        if created_time:
            if from_date <= created_time <= to_date:
                created += 1
            else:
                ## Count files modified this week
                if last_modified_time:
                    if from_date <= last_modified_time <= to_date:
                        modified += 1

        total_files += 1

    result = {
        "docs_created": created,
        "docs_edited": modified
    }

    return result


async def get_data(client):

    # Get the user's working hours and time zone
    user_time_zone = await (user(client))
    if not user_time_zone:
        print("❌ Unable to fetch user time zone information.")
        return

    time_zones = build_windows_to_iana_map()
    iana_time_zone = time_zones.get(user_time_zone["timeZone"].name, 'UTC')

    # Get past week's date range(Monday to Sunday)
    today = datetime.now(ZoneInfo(iana_time_zone))
    start_of_past_week = today - timedelta(days=today.weekday())  # Monday
    #start_of_past_week -= timedelta(weeks=1)  # Go back one week
    # Calculate the end of the week (Sunday)
    end_of_week = start_of_past_week + timedelta(days=6)  # Sunday
    from_date = start_of_past_week.replace(hour=0, minute=0, second=0, microsecond=0)
    to_date = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

    emails_inbox = await (get_mails(client,user_time_zone,iana_time_zone, from_date, to_date,"Inbox"))
    emails_sent = await (get_mails(client,user_time_zone,iana_time_zone, from_date, to_date,"SentItems"))
    events = await (get_events(client, user_time_zone, iana_time_zone, from_date, to_date))
    files = await (get_files(client, user_time_zone, iana_time_zone, from_date, to_date))

    # Merge results into a single dictionary, keeping the original keys
    result = emails_inbox.copy()
    result.update(emails_sent)
    result.update(events)
    result.update(files)

    return result

# Main function to run the script
async def main():

    # Get Microsoft Graph API token
    client = get_microsoft_graph_api_token(CLIENT_ID_MICROSOFT)

    # Get the user's working hours and time zone
    user_time_zone = await (user(client))
    if not user_time_zone:
        print("❌ Unable to fetch user time zone information.")
        return

    time_zones = build_windows_to_iana_map()
    iana_time_zone = time_zones.get(user_time_zone["timeZone"].name, 'UTC')

    # Get past week's date range(Monday to Sunday)
    today = datetime.now(ZoneInfo(iana_time_zone))
    start_of_past_week = today - timedelta(days=today.weekday())  # Monday
    start_of_past_week -= timedelta(weeks=1)  # Go back one week
    # Calculate the end of the week (Sunday)
    end_of_week = start_of_past_week + timedelta(days=6)  # Sunday
    from_date = start_of_past_week.replace(hour=0, minute=0, second=0, microsecond=0)
    to_date = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

    emails_inbox = await (get_mails(client,user_time_zone,iana_time_zone, from_date, to_date,"Inbox"))
    emails_sent = await (get_mails(client,user_time_zone,iana_time_zone, from_date, to_date,"SentItems"))
    events = await (get_events(client, user_time_zone, iana_time_zone, from_date, to_date))
    files = await (get_files(client, user_time_zone, iana_time_zone, from_date, to_date))

    # Merge results into a single dictionary, keeping the original keys
    result = emails_inbox.copy()
    result.update(emails_sent)
    result.update(events)
    result.update(files)

    print("\nResults:")
    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    #asyncio.run(main())
    client = get_microsoft_graph_api_token(CLIENT_ID_MICROSOFT)
    data = asyncio.run(get_data(client))
    print(data)
