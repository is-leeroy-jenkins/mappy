# Mistral AI API Setup Instructions

This guide explains how to create a Mistral AI account, generate an API key, and configure it for
local development with Foo.



## 1. Create a Mistral AI Account

1. Navigate to https://console.mistral.ai/
2. Create an account or sign in
3. Complete any required account verification



## 2. Open Mistral Studio

1. Open the Mistral Studio console
2. Confirm that Studio API access is enabled for the account or workspace
3. Review the available usage tier and rate limits

Mistral currently provides a free API mode with usage and rate limits. Billing may be required for
higher usage levels or specific account configurations.



## 3. Configure Billing (If Required)

1. Open the Mistral Admin or billing settings
2. Add a payment method when required by the selected usage tier
3. Review workspace usage limits and spending controls



## 4. Generate an API Key

1. Open **API Keys** in Mistral Studio
2. Select the target workspace if prompted
3. Click **Create new key**
4. Enter a descriptive name (e.g., foo-mistral)
5. Set an expiration date when appropriate
6. Configure connector access scope if the option is presented
7. Create the key
8. Copy the generated key immediately

The full key is displayed only when it is created. Store it securely because it cannot be retrieved
again after the creation dialog is closed.



## 5. Configure Environment Variable

Foo reads the Mistral credential from `MISTRAL_API_KEY`.

### Windows (PowerShell)

    setx MISTRAL_API_KEY "your-mistral-api-key"

Restart the terminal after running `setx`.

### macOS / Linux

    export MISTRAL_API_KEY="your-mistral-api-key"

To persist permanently:

    echo 'export MISTRAL_API_KEY="your-mistral-api-key"' >> ~/.bashrc

Restart the terminal or reload the shell configuration.



## 6. Verify Setup

### Windows (PowerShell)

    echo $env:MISTRAL_API_KEY

### macOS / Linux

    echo $MISTRAL_API_KEY

If configured correctly, the environment variable will contain the configured key.



## Security Best Practices

- Never commit API keys to version control.
- Do not embed keys directly in source files.
- Copy newly generated keys immediately and store them securely.
- Set expiration dates and rotate keys regularly when practical.
- Store production credentials in an approved secrets manager.
- Use separate keys or workspaces for development and production when practical.
- Review usage and rate limits periodically.