# Stock-Alarm Project

## Overview

The Stock-Alarm project is a simple tool designed to monitor stock data from a local dataset and notify users via email when specific thresholds are reached. This project aims to provide users with a convenient way to stay informed about changes in stock prices without the need for constant manual monitoring.

## Features
- [X] Lower Threshold
- [X] Upper Threshold
- [X] Multiple Threholds
- [X] Email the recipient when threshold reched
- [X] Notify dev/support when failure occurs

## Getting Started

### Prerequisites

- Python 3.x
- Resend API Key (Read more)[https://resend.com/]

### Installation

1. Clone the repository:
```bash
git clone https://github.com/khaifahmi99/stock-alarm.git
cd stock-alarm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Fill in the config/environment variables with your information:
```bash
cp example.env .env
``` 

4. Customize your watchlist and threshold. Edit the `./watchlist-us.json` file
5. Run the script, it will send you an email if the prices reached the threshold set
```bash
python3 main.py
```

### Configuring Database (Optional)
MongoDB is used to store the collection price for every run. This is an opt-in feature.
This is enabled by providing the `DATABASE_URL` in the environment variables.

To set up the mongoDB:
1. Fill in the `DATABASE_URL` in the `.env` file
2. Run `prisma db push` to provision the collection within the database (specified within the `DATABASE_URL`)

## Contributing
Contributions are welcome! If you have suggestions, feature requests, or bug reports, please create an issue or submit a pull request.

## License
TODO: Fill this one