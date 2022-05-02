# The GitBot Developer README 💻
This is the actual, useful README if you're planning to contribute, or you're simply curious.

## General info:
- `py-3.10` - the bot's current runtime is Python 3.10.0, you can always find the up-to-date runtime in `runtime.txt`
- `discord.py` - all of the Discord interfacing is handled by discord.py, I stuck with it even through the abandonment phase in late 2021-early 2022, it's well-developed and easy to use, with a massive and helpful community
- `MongoDB` - data is stored in a MongoDB Atlas-operated cluster. Interfacing is handled by [`motor`](https://motor.readthedocs.io/en/stable/)
- `text-based commands` - GitBot doesn't use slash commands for now, read more [here](#slash-commands)
- `syntax` - the commands are organized in groups that not only work just like CLI apps, but also make it easier to remember how to use them. The entirety of GitBot's command syntax is themed after [`git`](https://git-scm.com/)
- `dependencies` - the entire list of GitBot's dependencies can be found in `requirements.txt`
- `codestyle` - PEP8 all the way, more info in `CONTRIBUTING.md`

## Slash commands
This is a tough topic for me, as GitBot's developer, as I'm sure it is for more devs.
I want GitBot to last long, be of use to as many, and provide the best possible user experience.
Nonetheless, GitBot isn't a source of income for me, it's strictly pro-bono. Over the last year I've had less and less time to work on it.
For that reason, the news of the *de-facto deprecation of text-based bots* really worried me. 
**I don't support slash commands, they're buggy (at least for now), kill creativity and freedom, and are a massive, massive hassle to migrate to.**
The only light at the end of the tunnel is message intent verification, 
which I'm confident GitBot will pass due to its extensive use of the intent outside of commands alone.
If after submitting it, GitBot will be denied the intent, I'm going to be forced to step down and archive the project.
But let's not get ahead of ourselves. I plan to verify GitBot in July, and we'll worry then. For now, let's make the most of this amazing project.
