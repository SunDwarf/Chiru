## Chiru (散る)

[![Requirements Status](https://requires.io/github/SunDwarf/Chiru/requirements.svg?branch=master)](https://requires.io/github/SunDwarf/Chiru/requirements/?branch=master)

**Chiru** is a specific-purpose Discord bot.  It is not designed to be like the hundreds of dime-a-dozen bots that
try and do everything.

[Test Server]([https://discord.gg/tnBSBMU)
[Invite to your server](https://discordapp.com/oauth2/authorize?client_id=168643285475131392&scope=bot)


## Setup

Chiru has a slightly complex set up due to the database backend used.  
***Unless you have a C + C++ compiler set up for Python development on Windows, do not try and run on Windows.***

1. Install requirements.

	`pip install -r --upgrade requirements.txt`
	
	
2. Copy config.example.yml to config.yml.

	`cp config.example.yml config.yml`
	
	
3. Update the values as appropraite. 

4. Run the bot.

	`python3.5 bot.py config.yml`
	
5. Invite the bot to your server.

	The invite link is automatically generated