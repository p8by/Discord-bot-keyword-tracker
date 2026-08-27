# Discord-bot-keyword-tracker
A discord bot for counting how many times certain words have been said in a server.

---

It generates 4 other files when ran:

**admins.txt** - place UIDs in here to allow them to use the admin commands.

**config.txt** - place your discord bot token here

**keywords.txt** - where all the keywords are stored that the bot looks up, this can be edited in the file or when the discord bot is ran (if an admin)

**keyword_counts.json** - stores the data for each user

**phrases.txt** - where all the phrases the bot uses are looked up.

# Commands

Contains seven commands:

**/addkeyword** - adds a new keyword to the keywords.txt (admin only)

**/removekeyword** - removes a keyword from keywords.txt (admin only)

**/addphrase** - adds a phrase to phrases.txt (admin only)

**/removephrase** -removes a phrase from phrases.txt (admin only)

**/keywords** - shows a list of tracked keywords from keywords.txt

**/leaderboard** - two options, first one shows leaderboard for total amount of keywords said, second option shows how many times a certain keyword has been said by users

**/stats** view keyword stats for yourself or another user

**/phrases** Shows list of reply phrases

