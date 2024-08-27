# Authenticating for the Google APIs

The gcalcli needs to be granted permission to integrate with Google APIs for your account before it
can work properly.

These initial setup steps can look a little intimidating, but they're completely safe and similar
to the setup currently needed for most non-commercial projects that integrate with Google APIs
(for example, [gmailctl] or
[Home Assistant](https://www.home-assistant.io/integrations/google_assistant/)).

[gmailctl]: https://github.com/mbrt/gmailctl

## Part 1: Setting up your Google "project"

To generate an OAuth token, you first need a placeholder "project" in Google Cloud Console. Create
a new project if you don't already have a generic one you can reuse.

1. [Create a New Project](https://console.developers.google.com/projectcreate) within the Google
   developer console
  1. (You can skip to the next step if you already have a placeholder project you can use)
  2. Pick any project name. Example: "Placeholder Project 12345"
  3. Click the "Create" button.
2. [Enable the Google Calendar API](https://console.developers.google.com/apis/api/calendar-json.googleapis.com/)
  1. Click the "Enable" button.

## Part 2: Creating an auth client and token

Once you have the project with Calendar API enabled, you need a way for gcalcli to request
permission to use it on a user's account.

1. [Create OAuth2 consent screen](https://console.developers.google.com/apis/credentials/consent/edit;newAppInternalUser=false) for a "UI/Desktop Application".
   1. Fill out required App information section
      1. Specify App name. Example: "gcalcli"
      2. Specify User support email. Example: your@gmail.com
   2. Fill out required Developer contact information
      1. Specify Email addresses. Example: your@gmail.com
   3. Click the "Save and continue" button.
   4. Scopes: click the "Save and continue" button.
   5. Test users
      1. Add your@gmail.com
      2. Click the "Save and continue" button.
2. [Create OAuth Client ID](https://console.developers.google.com/apis/credentials/oauthclient)
   1. Specify Application type: Desktop app.
   2. Click the "Create" button.
3. Grab your newly created Client ID (in the form "xxxxxxxxxxxxxxx.apps.googleusercontent.com") and Client Secret from the Credentials page.

You'll give these values to gcalcli to use in its setup flow.

## Last part: gcalcli auth setup

Use those client ID and secret values to finish granting gcalcli permission to access your
calendar.

Run gcalcli passing a `--client-id`:

```shell
$ gcalcli --client-id=xxxxxxxxxxxxxxx.apps.googleusercontent.com list
```

If it isn't already set up with permission, it will prompt you through remaining steps to enter
your client secret, launch a browser to log into Google and grant permission.

If it completes successfully you'll see a list of your Google calendars in the cli.

NOTE: You'll generally see a big scary security warning page during this process and need to click
"Advanced > Go to gcalcli (unsafe)" during this process because it's running a local setup flow for
a non-Production client project.

## FAQ

### Can you make this easier?

Probably not, unless Google makes changes to allow simpler authorization for non-commercial
projects.

See https://github.com/insanum/gcalcli/issues/692 for details.

### Is this really secure?

Yes, totally secure. The scary security warnings aren't relevant to this kind of usage.

The warnings in the browser are to protect against phishing by impersonating another project's
"client" to trick users into trusting it.

It's best to avoid sharing the client secret. Those credentials could allow someone to impersonate
gcalcli and use the permission you've granted it to access your private calendars (though other
Google security protections would probably make that difficult to exploit in practice).
