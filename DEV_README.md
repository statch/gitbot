# The GitBot Developer README 💻
This is a useful README if you're planning to contribute, or you're simply curious.

## General info:
- `py-3.11` - the bot's current runtime is Python 3.11, you can always find the up-to-date runtime in `runtime.txt`
- `discord.py` - all of the Discord interfacing is handled by discord.py, I stuck with it even through the abandonment phase in late 2021/early-2022, it's well-developed and easy to use, with a massive and helpful community
- `MongoDB` - data is stored in a MongoDB Atlas-operated cluster. Interfacing is handled by [`motor`](https://motor.readthedocs.io/en/stable/)
- `text-based commands` - GitBot doesn't use slash commands, intead, it uses a git-themed syntax mentioned below
- `syntax` - the commands are organized in groups that not only work just like CLI apps, but also make it easier to remember how to use them. The entirety of GitBot's command syntax is themed after [`git`](https://git-scm.com/)
- `dependencies` - the entire list of GitBot's dependencies can be found in `requirements.txt`
- `codestyle` - PEP8 all the way, more info in `CONTRIBUTING.md`
