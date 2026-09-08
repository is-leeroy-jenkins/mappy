# Claude (Anthropic) API Setup Instructions

This guide explains how to create an Anthropic account, generate a Claude API key, and configure it
for local development with Foo.



## 1. Create an Anthropic Account

1. Navigate to https://console.anthropic.com/
2. Create an account or sign in
3. Complete any required account verification



## 2. Enable Claude API Access

1. Open the Anthropic Console
2. Confirm that API access is available for the workspace
3. Review the available usage tier, rate limits, and model access



## 3. Configure Billing or Credits (If Required)

1. Open the Anthropic Console billing settings
2. Add billing information or usage credits when required by the account tier
3. Review usage limits and spending controls



## 4. Generate an API Key

1. Open the API Keys section in the Anthropic Console
2. Click **Create Key**
3. Enter a descriptive name (e.g., foo-claude)
4. Copy the generated API key

Example key format:

    sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

Store the key securely. Treat it as a secret and do not commit it to source control.



## 5. Configure Environment Variable

Foo reads the Claude credential from `CLAUDE_API_KEY`.

### Windows (PowerShell)

    setx CLAUDE_API_KEY "sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"

Restart the terminal after running `setx`.

### macOS / Linux

    export CLAUDE_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"

To persist permanently:

    echo 'export CLAUDE_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc

Restart the terminal or reload the shell configuration.



## 6. Verify Setup

### Windows (PowerShell)

    echo $env:CLAUDE_API_KEY

### macOS / Linux

    echo $CLAUDE_API_KEY

If configured correctly, the environment variable will contain the configured key.



## Security Best Practices

- Never commit API keys to version control.
- Do not embed keys directly in source files.
- Store production credentials in an approved secrets manager.
- Use separate keys for development and production when practical.
- Rotate keys immediately if they are exposed.
- Review usage and rate limits periodically.