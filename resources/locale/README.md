# 🌐 GitBot Localization
*Here you can contribute to the accessibility of GitBot by providing translations of commands.*

# Adding a locale

## Prerequistites
Localizing GitBot doesn't require any programming knowledge (Although it can certainly come in handy). What it does require, however, is basic knowledge of [JSON syntax](https://www.w3schools.com/js/js_json_syntax.asp), GitHub/git, and very good knowledge of both the target language and English. With GitBot's code and UI we aim for quality, and with translations we want to deliver the same - no Google Translate jankery with this one.

## Overview
### Getting started
To get your hands dirty translating, [fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo), and commit your work there. Then simply create a PR implementing your changes.

### Structure
As you can see locales are stored as JSON files, named after their ISO Alpha-2 codenames.  
Each locale has an entry in `index.json`'s `languages` field equivalent to its meta-attributes.

### Meta field
Meta attributes are essential for GitBot to know where to look for a specific locale.

```json
{
  "name": "pl",
  "full_name": "polish",
  "localized_name": "polski",
  "flag": ":flag_pl:" 
}
```

#### Let's break this down
- `name` - ISO Alpha-2 codename of the language  
- `full_name` - Full name of the language in english  
- `localized_name` - Local name of the language  
- `flag` - Discord-markdown name of the language's flag  

And that's a `meta` field done! Now simply add it to the `languages` field in `index.json` as the last one:

```json
{
  "master": "en",
  "languages": [
    "...",
    {
      "YOUR_LOCALE": "HERE"
    }
  ]
}
```

## Locale file
As mentioned in the beginning, locales are JSON files with names being their `name` meta attribute (`pl.json` for Polish).
After creating it, copy the contents of the English locale (`en.json`) as it's the only one that is *always* up to date. Then, replace the `meta` field with the one you created earlier. After having done that, you can start on translating in compliance with the [guidelines](#localization-guidelines)!

# General localization guidelines
- You don't translate keys, only the values
- Keep capitalization/punctuation consistent
- The meaning must always stay the same
- Newlines are there to separate sections, or keep the lines from being too long - make sure everything looks and feels right
- Every `{X}` placeholder must be kept, if you can't figure out what it represents, look in the code or ask in the Discussions tab/Discord
- Keep markdown/hyperlinks consistent wherever possible

# Specifics
Some fields (sometimes called sections) require special care and attention (don't we all?). Ones aren't supposed to be translated, others need to be filled out in a specific manner. You can read all about that below!

## Help
The `help` section is very important to be kept up-to-date, since it allows us to keep users happy and reduce their confusion regarding some more complex commands.  
**Every entry in this section's `commands` subfield follows this format**:
```json
"command_name": {
  "brief": "A brief command description",
  "usage": "command signature [with_args]",
  "example": "command --usage example",
  "description": "A detailed description",
  "argument_explainers": [
    "a_list",
    "of_arguments",
    "used_in_the_command"
  ],
  "qa_resource": "If the command uses a quick-access resource (user, org, repo or null)",
  "required_permissions": ["THE_PERMISSIONS", "REQUIRED", "TO_RUN_THE_COMMAND"]
}
```
Now, there are some important things to mention:
- **The following subfields should remain unchanged** (They don't vary from language to language, since they depend on other fields that *are* supposed to be changed):
  - `usage`
  - `example`
  - `arguments_explainers`
  - `qa_resource`
  - `required_permissions`  

# Something's not very clear?
If you have any questions regarding the localization process, need help, or just want to talk - join our [**Discord!**](https://discord.statch.org) *(I promise we don't bite!)*

*Thank you for being such an important part of the GitBot family* ♥️
