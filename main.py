from __future__ import print_function

import datetime
import os.path
from sys import argv
import discord
from discord.ext import commands
from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
primary = 'primary'
programming = 'ALT CALENDAR ID'
workOut = 'ALT CALENDAR ID'
study = 'ALT CALENDAR ID'

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix = '!', intents=discord.Intents.all())
       
async def main(action, calendar_type, duration=None, start_time=None, description=None, ctx=None):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('../token.json'):
        creds = Credentials.from_authorized_user_file('../token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../token.json', 'w') as token:
            token.write(creds.to_json())
    if action == 'add':
        if calendar_type == 'Main':
            type = primary
            addEvent(creds, start_time, duration, description, type)
        if calendar_type == 'Coding':
            type = programming
            addEvent(creds, start_time, duration, description, type)
        if calendar_type == 'Workout':
            type = workOut
            addEvent(creds, start_time, duration, description, type)
        if calendar_type == 'Study':
            type = study
            addEvent(creds, start_time, duration, description, type)
            
    if action == 'commit':
        if calendar_type == 'Main':
            type = primary
            await commitHours(creds, type, ctx)
        if calendar_type == 'Coding':
            type = programming
            await commitHours(creds, type, ctx)
        if calendar_type == 'Workout':
            type = workOut
            await commitHours(creds, type, ctx)
        if calendar_type == 'Study':
            await commitHours(creds, type, ctx)

@bot.command()
async def commitHours(creds, type, ctx):

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        today = datetime.date.today()  # 'Z' indicates UTC time
        timeStart = str(today) + "T08:00:00-05:00"
        timeEnd = str(today) + "T23:59:59-05:00"
        print("Getting today's events")
        await ctx.send("Getting today's events")
        events_result = service.events().list(calendarId=type, timeMin=timeStart, timeMax=timeEnd, singleEvents=True, orderBy='startTime', timeZone='Canada/Toronto').execute()

        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            await ctx.send('No upcoming events found.')
            return []

        total_duration = datetime.timedelta(
            seconds=0,
            minutes=0,
            hours=0,
        )
        events_data = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            start_formatted = parser.isoparse(start).strftime("%Y-%m-%d %H:%M:%S")
            end_formatted = parser.isoparse(end).strftime("%Y-%m-%d %H:%M:%S")
            duration = parser.isoparse(end) - parser.isoparse(start)

            events_data.append({
                'summary': event['summary'],
                'start_time': start_formatted,
                'end_time': end_formatted,
                'duration': duration.total_seconds(),
            })


            if type == primary:
                print(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
                await ctx.send(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")

            elif type == programming:
                total_duration += duration
                print(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
                await ctx.send(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
            
            elif type == workOut:
                total_duration += duration
                print(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
                await ctx.send(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
            
            elif type == study:
                total_duration += duration
                print(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")
                await ctx.send(f"{event['summary']}, start time: {start_formatted}, duration: {duration}")

        if type == primary:
            print(f"No more events")
            await ctx.send(f"No more events")

        elif type == programming:
            print(f"Total coding time: {total_duration}")
            await ctx.send(f"Total coding time: {total_duration}")

        elif type == workOut:
            print(f"Total workout time: {total_duration}")
            await ctx.send(f"Total workout time: {total_duration}")
        
        elif type == study:
            print(f"Total studying time: {total_duration}")
            await ctx.send(f"Total studying time: {total_duration}")
        return events_data
    except HttpError as error:
        print('An error occurred: %s' % error)
        await ctx.send('An error occurred: %s' % error)
        return []



def addEvent(creds, start_time, duration, description, type):
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')

    end = start_time + datetime.timedelta(hours=int(duration))
    start_formatted = start_time.isoformat() + '-05:00'
    end_formatted = end.isoformat() + '-05:00'

    event = {
        "summary": description,
        "colorID": 2,
        "start": {
            "dateTime": start_formatted,
            "timeZone": "GMT-04:00",
        },
        "end": {
            "dateTime": end_formatted,
            "timeZone": "GMT-04:00",
        },
    }
    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId=type, body=event).execute()

@bot.command()
async def commit(ctx, *args):
    command = ' '.join(args)

    parts = command.split()

    if len(parts) == 1:
        action = 'commit'
        calendar_type = parts[0]
        await main(action, calendar_type, ctx=ctx)
        


@bot.command()
async def add(ctx, *args):
    # Join the arguments into a single string
    command = ' '.join(args)

    # Split the command into individual parts
    parts = command.split()

    if len(parts) >= 4:
        action = 'add'
        calendar_type = parts[0]
        duration = parts[1]
        start_time = parts[2]
        description = ' '.join(parts[3:])

        await main(action, calendar_type, duration, start_time, description)



bot.run('YOUR DISCORD BOT TOKEN') 



if __name__ == '__main__':
    main()

