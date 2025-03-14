# Formance Ledger Version 2 Backoffice

## Overview

Formance Ledger Version 2 Backoffice is a comprehensive management interface for the Formance Ledger system. This application provides a user-friendly dashboard to monitor, manage, and interact with ledgers, accounts, transactions, and assets within the Formance ecosystem.

## Features

This backoffice UI implements basic functionalities for:

- Multi-Ledger Support
- Account Management
- Transaction Monitoring
- Asset Overview
- Interactive Visualizations
- Real-time Updates

## Installation

1. Clone the repository:
```
git clone https://github.com/your-repo/formance-ledger-v2-backoffice.git
cd formance-ledger-v2-backoffice
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables:
```
export FORMANCE_API_URL=http://your-ledger-api-url:3068
export SHOW_TRANSACTION_FORM=true
```

4. Run the application:
```
streamlit run ledger_ui.py
```


## Local Testing

To test the UI locally:

1. Ensure you have Docker and Docker Compose installed on your system.

2. Clone the repository:
```
git clone https://github.com/your-repo/formance-ledger-v2-backoffice.git
cd formance-ledger-v2-backoffice
```

3. Start the Formance Ledger services and the Streamlit UI:
```
docker-compose up -d --build
```


4. Access the UI in your browser at http://localhost:8501

The compose file already sets the necessary environment variables, including FORMANCE_API_URL and SHOW_TRANSACTION_FORM, so no additional configuration is required for local testing.

## Environment Variables

- `FORMANCE_API_URL`: The URL of your Formance Ledger API (default: `http://ledger:3068`)
- `SHOW_TRANSACTION_FORM`: Set to `true` to enable the transaction creation form (default: `false`)

## Usage

Use the sidebar navigation menu to switch between different views:

- Ledgers
- Accounts
- Transactions
- Assets

## Dependencies

- Python 3.9+
- Streamlit
- Pandas
- Plotly
- Networkx
- Matplotlib

## License

This project is based on the open-source [Formance Ledger](https://github.com/formancehq/ledger), which is licensed under the MIT license. You may use, modify, and distribute this backoffice dashboard under similar permissive terms.

## References

This project is based on the open-source Formance Ledger. For more information about the underlying ledger system, please visit:

[Formance Ledger GitHub Repository](https://github.com/formancehq/ledger)