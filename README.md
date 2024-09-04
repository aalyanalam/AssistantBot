# Assistant Bot

This project is written in Python and connects the user's personal Google Calender to their own Discord Bot.
The user is then able to list events taking place that day by using the "!commit" command, which then lists all the user's events with their details for the day.
Using the "!commit" command will also store the events as well as how many hours each event is in a SQL database.
The program also allows the user to add events to their calender through their discord bot by using the "!add" command.
This command allows the user to create an event and also specify the name of the event, which calender to add the event to and the time and date of the event.
The "!add" command also utilizes the Gemini AI API so that the user can type in a more natural way when using the command.
For example, without Gemini the user would type out "!add study "2024-08-25T09:00:00Z" "Digital"", but with Gemini the user can
type something more natural such as "!add Add a study session called Digital for 1 hours starting today at 6 PM".

# Built With
- Python
- Google Calendar API
- Discord API
- Gemini API
