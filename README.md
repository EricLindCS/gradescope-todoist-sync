# Gradescope-Todo Sync

An unofficial Gradescope API that syncs assignments to Todoist.

## Table of Contents

- Introduction
- Features
- Requirements
- Installation
- Configuration
- [Running Locally](#running-locally)
- [Deploying to a Web Platform](#deploying-to-a-web-platform)
- Usage
- Contributing
- License

## Introduction

This project provides a way to sync assignments from Gradescope to Todoist. It uses Flask to create a web server that handles the synchronization process.

## Features

- Sync Gradescope assignments to Todoist.
- Schedule automatic synchronization.
- Simple and easy-to-use API.

## Requirements

- Python 3.6 or higher
- [Todoist API Key](https://developer.todoist.com/)
- [Gradescope Account](https://www.gradescope.com/)

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/ericlindcs/gradescope-calendar-sync.git
    cd gradescope-calendar-sync
    ```

2. **Create a virtual environment:**

    ```sh
    python -m venv env
    source env/Scripts/activate  # On Windows
    # source env/bin/activate    # On macOS/Linux
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. **Create a `.env` file in the root directory:**

    ```sh
    touch .env
    ```

2. **Add the following environment variables to the `.env` file:**

    ```env
    TODOIST_API_KEY=your_todoist_api_key
    GRADESCOPE_USER=your_gradescope_email
    GRADESCOPE_PASSWORD=your_gradescope_password
    # Optional: Pensieve (requires a Google-authenticated session cookie)
    # Get a browser session cookie for pensieve.co after signing in with Google and set it here.
    PENSIEVE_COOKIE=your_pensieve_session_cookie_string
    ```

Notes about Pensieve integration:
- Pensieve currently requires Google-based authentication. This project supports a cookie-based approach: set `PENSIEVE_COOKIE` to a valid authenticated session cookie for `pensieve.co` (for example the `connect.sid` or full cookie header as needed). This is a pragmatic workaround for headless syncing; you may need to extract the cookie from your browser's developer tools.
- Once configured, the sync script will attempt to list classes and fetch assignments from Pensieve and include them alongside Gradescope/Canvas courses.
- This cookie-based approach is less secure than an OAuth flow — treat the cookie like a secret and avoid committing it to source control.
## Running Locally

1. **Activate the virtual environment:**

    ```sh
    source env/Scripts/activate  # On Windows
    # source env/bin/activate    # On macOS/Linux
    ```

2. **Run the Flask application:**

    ```sh
    python app.py
    ```

3. **Open your browser and navigate to:**

    ```
    http://127.0.0.1:5000
    ```

    You should see a message indicating that the task sync app is running.

## Deploying to a Web Platform

### Deploying to Heroku

1. **Install the Heroku CLI:**

    Follow the instructions [here](https://devcenter.heroku.com/articles/heroku-cli).

2. **Login to Heroku:**

    ```sh
    heroku login
    ```

3. **Create a new Heroku app:**

    ```sh
    heroku create your-app-name
    ```

4. **Add the Heroku remote:**

    ```sh
    git remote add heroku https://git.heroku.com/your-app-name.git
    ```

5. **Set the environment variables on Heroku:**

    ```sh
    heroku config:set TODOIST_API_KEY=your_todoist_api_key
    heroku config:set GRADESCOPE_USER=your_gradescope_email
    heroku config:set GRADESCOPE_PASSWORD=your_gradescope_password
    ```

6. **Deploy the app to Heroku:**

    ```sh
    git push heroku main
    ```

7. **Open the app in your browser:**

    ```sh
    heroku open
    ```

### Deploying to Other Platforms

For other platforms like AWS, Google Cloud, or Azure, follow their respective documentation to deploy a Flask application. Ensure that you set the required environment variables and install the necessary dependencies.

## Usage

Once the application is running, it will automatically sync your Gradescope assignments to Todoist based on the schedule defined in the [`app.py`] file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License. See the LICENSE file for details.