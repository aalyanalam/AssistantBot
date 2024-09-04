from __future__ import print_function
import unicodedata
import datetime
import os.path
import re
from sys import argv
import sqlite3
import discord
from discord.ext import commands
from dateutil import parser
from datetime import timedelta
import google.generativeai as genai  # Import the Google AI module
import random
import unicodedata
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
botToken = os.getenv("botToken")
geminiKey = os.getenv("geminiKey")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
primary = 'primary'
programming = os.getenv("programmingID")
workOut = os.getenv("workoutID")
study = os.getenv("studyID")

genai.configure(api_key=geminiKey)
model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

def parse_relative_date(relative_date_str):
    """Handles relative date strings like 'tomorrow'."""
    relative_date_str = relative_date_str.lower()
    if "tomorrow" in relative_date_str:
        return (datetime.datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d') + " " + relative_date_str.split(" at ")[1]
    elif "today" in relative_date_str:
        return datetime.datetime.now().strftime('%Y-%m-%d') + " " + relative_date_str.split(" at ")[1]
    else:
        # If no relative date found, return the original string
        return relative_date_str

async def main(action, calendar_type, duration=None, start_time=None, description=None, ctx=None):
    print(f"Main function called with action={action}, calendar_type={calendar_type}, duration={duration}, start_time={start_time}, description={description}")
    creds = None
    if os.path.exists("token.json"):
        print("Loading credentials from token.json")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        print("No token.json found. Running OAuth2 flow.")
    
    if not creds or not creds.valid:
        print("Credentials are not valid or expired.")
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Token refreshed successfully.")
            except Exception as e:
                print(f"Error refreshing token: {e}")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("New credentials obtained.")
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            print("Credentials saved to token.json")
    
    if action == 'add':
        print(f"Adding event to {calendar_type} calendar.")
        if calendar_type == 'Main':
            type = primary
            addEvent(creds, start_time, duration, description, type)
        elif calendar_type == 'Coding':
            type = programming
            addEvent(creds, start_time, duration, description, type)
        elif calendar_type == 'Workout':
            type = workOut
            addEvent(creds, start_time, duration, description, type)
        elif calendar_type == 'Study':
            type = study
            addEvent(creds, start_time, duration, description, type)
            
    if action == 'commit':
        print(f"Committing hours for {calendar_type} calendar.")
        if calendar_type == 'Main':
            type = primary
            await commitHours(creds, type, 'Main', ctx)
        elif calendar_type == 'Coding':
            type = programming
            await commitHours(creds, type, 'Coding', ctx)
        elif calendar_type == 'Workout':
            type = workOut
            await commitHours(creds, type, 'Workout', ctx)
        elif calendar_type == 'Study':
            type = study
            await commitHours(creds, type, 'Study', ctx)


async def commitHours(creds, type, calendar_type, ctx):
    print(f"commitHours called for calendar {calendar_type}")
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar service built successfully.")

        today = datetime.date.today()
        timeStart = str(today) + "T08:00:00-05:00"
        timeEnd = str(today) + "T23:59:59-05:00"
        print(f"Getting today's events from {timeStart} to {timeEnd}")
        await ctx.send("Getting today's events")
        events_result = service.events().list(
            calendarId=type,  # type is the calendar ID
            timeMin=timeStart,
            timeMax=timeEnd,
            singleEvents=True,
            orderBy='startTime',
            timeZone='Canada/Toronto'
        ).execute()

        print(f"API response: {events_result}")

        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            await ctx.send('No upcoming events found.')
            return []

        print(f"Number of events found: {len(events)}")
        total_duration = datetime.timedelta(
            seconds=0,
            minutes=0,
            hours=0,
        )

        # Open SQLite database
        conn = sqlite3.connect('hours.db')
        cur = conn.cursor()
        print("Opened database successfully")

        # Iterate over the events and calculate total duration
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            print(f"Processing event: {event}")

            start_formatted = parser.isoparse(start).strftime("%Y-%m-%d %H:%M:%S")
            end_formatted = parser.isoparse(end).strftime("%Y-%m-%d %H:%M:%S")
            duration = parser.isoparse(end) - parser.isoparse(start)

            total_duration += duration

            # Prepare event data to be inserted into the database
            event_summary = event.get('summary', 'Unnamed event')
            event_duration_hours = duration.total_seconds() / 3600

            # Insert into SQLite database
            cur.execute("INSERT INTO hours (DATE, CATEGORY, HOURS) VALUES (?, ?, ?)",
                        (start_formatted, event_summary, event_duration_hours))

            print(f"Event added to database: {event_summary}, start: {start_formatted}, duration: {event_duration_hours} hours")

            # Send event summary to Discord channel
            await ctx.send(f"{event_summary}, start time: {start_formatted}, duration: {duration}")

        conn.commit()
        conn.close()

        # Output total hours for the day
        await ctx.send(f"Total duration for {calendar_type}: {total_duration}")
        print(f"Total duration for {calendar_type}: {total_duration}")

    except HttpError as error:
        print(f'An error occurred: {error}')
        await ctx.send(f'An error occurred: {error}')
        return []


def addEvent(creds, start_time, duration, description, type):
    print(f"addEvent called with start_time={start_time}, duration={duration}, description={description}, type={type}")
    try:
        # Parse the start_time string into a datetime object
        start_time = datetime.datetime.fromisoformat(start_time)

        # Calculate the end time by adding the duration to the start time
        end = start_time + datetime.timedelta(hours=int(duration))
        
        # Format the start and end times for the event with the correct timezone
        start_formatted = start_time.isoformat()
        end_formatted = end.isoformat()

        event = {
            "summary": description,
            "colorID": 2,
            "start": {
                "dateTime": start_formatted,
                "timeZone": "America/Toronto",  # Correct timezone for Toronto
            },
            "end": {
                "dateTime": end_formatted,
                "timeZone": "America/Toronto",  # Correct timezone for Toronto
            },
        }
        service = build('calendar', 'v3', credentials=creds)
        print("Inserting event into calendar.")
        event = service.events().insert(calendarId=type, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"An error occurred in addEvent: {e}")


@bot.command()
async def commit(ctx, *args):
    print(f"commit command called with args={args}")
    command = ' '.join(args)

    parts = command.split()

    if len(parts) == 1:
        action = 'commit'
        calendar_type = parts[0]
        print(f"Calling main with action={action} and calendar_type={calendar_type}")
        await main(action, calendar_type, ctx=ctx)

# Updated add command to handle natural language input
@bot.command()
async def add(ctx, *, args):
    print(f"add command called with args={args}")

    # Update the regular expression to capture the event name (called <name>)
    match = re.match(r'Add a (?P<calendar_type>\w+) session called (?P<event_name>.+?) for (?P<duration>\d+) hours? starting (?P<start_time>.+)', args)
    if match:
        calendar_type = match.group('calendar_type').capitalize()
        event_name = match.group('event_name').capitalize()  # Capture the event name
        duration = match.group('duration')

        # Convert relative dates (e.g., "tomorrow at 10 AM") to a specific datetime string
        start_time_str = parse_relative_date(match.group('start_time'))
        
        try:
            start_time = parser.parse(start_time_str).isoformat()
        except parser.ParserError as e:
            print(f"Error parsing start time: {e}")
            await ctx.send(f"Sorry, I couldn't understand the date and time format: {start_time_str}. Please try again.")
            return

        # Include the event name in the description
        description = f"{calendar_type} session: {event_name}"

        print(f"Parsed input: calendar_type={calendar_type}, event_name={event_name}, duration={duration}, start_time={start_time}, description={description}")
        
        # Call the main function to add the event
        await main('add', calendar_type, duration, start_time, description)

        # AI-generated response after event creation
        try:
            prompt = "Come up with a unique response to confirm an event has been created."
            response = model.generate_content(prompt)  # Corrected to generate_content

            # Get the AI-generated text and split into options
            ai_message = response.text.strip()

            # Strip out non-ASCII characters to avoid encoding errors
            ai_message_ascii = unicodedata.normalize('NFKD', ai_message).encode('ascii', 'ignore').decode('ascii')

            # Split the response into individual lines, removing empty lines
            responses = [line for line in ai_message_ascii.splitlines() if line.strip()]

            # Randomly select a response
            selected_response = random.choice(responses)
            print(f"AI-generated message: {selected_response}")

            # Send the selected AI-generated message to the user, without any prefix
            await ctx.send(selected_response)

        except Exception as e:
            print(f"Error generating AI response: {e}")
            await ctx.send(f"Sorry, there was an issue generating the AI response.")
    else:
        print("Failed to parse input. Sending error message to user.")
        await ctx.send("Sorry, I couldn't understand that command. Please try again.")



bot.run(botToken) 

if __name__ == '__main__':
    print("Main function is being called directly.")
    main()