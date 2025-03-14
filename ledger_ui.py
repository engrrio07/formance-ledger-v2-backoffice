import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime, timedelta
import os

# Define the default API endpoint
BASE_URL = os.environ.get('FORMANCE_API_URL', "http://ledger:3068")

# UI Setup
st.set_page_config(
    page_title="Formance Ledger Management v2",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Formance Ledger Management v2")

CURRENT_TIME = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

# Helper functions
def get_server_info():
    combined_info = {}
    version_info = None
    
    try:
        response1 = requests.get(f"{BASE_URL}/_/info")
        if response1.status_code == 200:
            version_info = response1.json().get("version")
    except Exception as e:
        st.error(f"Error fetching /_/info: {str(e)}")
    
    try:
        response2 = requests.get(f"{BASE_URL}/_info")
        if response2.status_code == 200:
            combined_info.update(response2.json().get('data', {}))
    except Exception as e:
        st.error(f"Error fetching /_info: {str(e)}")
    
    if version_info:
        combined_info["version"] = version_info
    
    return combined_info if combined_info else None

def list_ledgers():
    try:
        response = requests.get(f"{BASE_URL}/v2")
        if response.status_code == 200:
            return response.json()['cursor']['data']
        return []
    except Exception as e:
        st.error(f"Error listing ledgers: {str(e)}")
        return None

def get_ledger_info(ledger: str):
    try:
        response = requests.get(f"{BASE_URL}/{ledger}/_info")
        return response.json()['data'] if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching ledger info: {str(e)}")
        return None

def get_accounts(ledger: str = None):
    if ledger:
        try:
            response = requests.get(f"{BASE_URL}/{ledger}/accounts")
            if response.status_code == 200:
                accounts = response.json().get('cursor', {}).get('data', [])
                for acc in accounts:
                    acc['ledger'] = ledger
                return accounts
            return []
        except Exception as e:
            st.error(f"Error fetching accounts: {str(e)}")
            return []
    else:
        # Get accounts from all ledgers
        all_accounts = []
        ledgers = list_ledgers()
        for l in ledgers:
            try:
                response = requests.get(f"{BASE_URL}/{l['name']}/accounts")
                if response.status_code == 200:
                    accounts = response.json().get('cursor', {}).get('data', [])
                    for acc in accounts:
                        acc['ledger'] = l['name']
                    all_accounts.extend(accounts)
            except Exception:
                pass
        return all_accounts

def get_transactions(ledger: str = None, source: str = None, destination: str = None):
    params = {}
    if source and source.strip():
        params['source'] = source
    if destination and destination.strip():
        params['destination'] = destination
    
    if ledger:
        try:
            url = f"{BASE_URL}/{ledger}/transactions"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                transactions = response.json().get('cursor', {}).get('data', [])
                for tx in transactions:
                    tx['ledger'] = ledger
                return transactions
            return []
        except Exception as e:
            st.error(f"Error fetching transactions: {str(e)}")
            return []
    else:
        # Get transactions from all ledgers
        all_transactions = []
        ledgers = list_ledgers()
        for l in ledgers:
            try:
                url = f"{BASE_URL}/{l['name']}/transactions"
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    transactions = response.json().get('cursor', {}).get('data', [])
                    for tx in transactions:
                        tx['ledger'] = l['name']
                    all_transactions.extend(transactions)
            except Exception:
                pass
        return all_transactions

def get_transaction(ledger: str, tx_id: str):
    try:
        response = requests.get(f"{BASE_URL}/{ledger}/transactions/{tx_id}")
        return response.json()['data'] if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching transaction: {str(e)}")
        return None

def get_account(ledger: str, address: str):
    try:
        response = requests.get(f"{BASE_URL}/{ledger}/accounts/{address}")
        return response.json()['data'] if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching account: {str(e)}")
        return None

def generate_transaction_graph(tx):
    # Create a graph visualization for transaction
    G = nx.DiGraph()
    
    for posting in tx.get('postings', []):
        src = posting.get('source')
        dst = posting.get('destination')
        amount = posting.get('amount')
        asset = posting.get('asset')
        
        G.add_node(src)
        G.add_node(dst)
        G.add_edge(src, dst, label=f"{asset} {amount}")
    
    pos = nx.spring_layout(G)
    fig, ax = plt.subplots(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=1500, font_size=10, ax=ax)
    nx.draw_networkx_edge_labels(G, pos, 
                              edge_labels=nx.get_edge_attributes(G, 'label'))
    
    # Convert to base64 for display in Streamlit
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def get_all_assets():
    all_assets = set()
    for ledger in list_ledgers():
        accounts = get_accounts(ledger['name'])
        for account in accounts:
            if account is not None:
                acc = get_account(ledger['name'], account['address'])
                if acc is not None:
                    all_assets.update(acc.get('balances', {}).keys())
    return list(all_assets)

# Server info sidebar
server_info = get_server_info()
with st.sidebar:
    st.header("Server Status")
    st.write(f"**Current Time**: {CURRENT_TIME}")
    
    if server_info:
        st.subheader("System Info")
        st.write(f"**Version**: {server_info.get('version', 'N/A')}")
        storage_info = server_info.get('config', {}).get('storage', {})
        st.write(f"**Storage Driver**: {storage_info.get('driver', 'N/A')}")
    
    st.markdown("---")

# Main navigation
view = st.sidebar.radio("Views", ["Ledgers", "Accounts", "Transactions", "Assets"])

# State management
if 'selected_ledger' not in st.session_state:
    st.session_state['selected_ledger'] = None
if 'selected_tx_id' not in st.session_state:
    st.session_state['selected_tx_id'] = None
if 'selected_account' not in st.session_state:
    st.session_state['selected_account'] = None
if 'view_tx_details' not in st.session_state:
    st.session_state['view_tx_details'] = False
if 'view_account_details' not in st.session_state:
    st.session_state['view_account_details'] = False
if 'source_filter' not in st.session_state:
    st.session_state['source_filter'] = ""
if 'destination_filter' not in st.session_state:
    st.session_state['destination_filter'] = ""
if 'account_ledger_filter' not in st.session_state:
    st.session_state['account_ledger_filter'] = None

# Function to reset view states
def reset_view_states():
    st.session_state['view_tx_details'] = False
    st.session_state['view_account_details'] = False

def update_filter():
    st.session_state['account_ledger_filter'] = st.session_state['temp_filter']
    st.session_state['selected_ledger'] = st.session_state['temp_filter']
    st.session_state['view_account_details'] = False
    st.session_state['selected_account'] = None

# 1. Ledgers View
if view == "Ledgers":
    reset_view_states()
    st.header("Ledgers Overview")
    
    # Show list of ledgers
    ledgers = list_ledgers()
    if ledgers:
        ledger_df = pd.DataFrame([{"Name": l['name']} for l in ledgers])
        
        # Allow selecting a ledger
        selected_index = st.selectbox(
            "Select a ledger:",
            range(len(ledger_df)),
            format_func=lambda i: ledger_df.iloc[i]['Name'],
            key="ledger_selection"
        )

        st.session_state['selected_ledger'] = ledger_df.iloc[selected_index]['Name']
        
        # Show summary for selected ledger
        ledger = st.session_state['selected_ledger']
        st.subheader(f"Summary for {ledger}")
        
        col1, col2 = st.columns(2)
        
        # Count accounts and transactions
        accounts = get_accounts(ledger)
        transactions = get_transactions(ledger)
        
        with col1:
            st.metric("Total Accounts", len(accounts))
        
        with col2:
            st.metric("Total Transactions", len(transactions))
        
        # Show migration history
        st.subheader("Migration History")
        ledger_info = get_ledger_info(ledger)
        
        if ledger_info and ledger_info.get('storage', {}).get('migrations'):
            migrations = ledger_info['storage']['migrations']
            migrations_df = pd.DataFrame(migrations)
            
            # Calculate durations
            migrations_df['start'] = pd.to_datetime(migrations_df['date'])
            migrations_df['end'] = pd.to_datetime(migrations_df.get('terminatedAt', migrations_df['date']))
            migrations_df['duration'] = (migrations_df['end'] - migrations_df['start']).dt.total_seconds().round(2)
            
            st.dataframe(
                migrations_df[['version', 'name', 'state', 'date', 'duration']].rename(columns={
                    "version": "Version",
                    "name": "Migration Name",
                    "state": "Status",
                    "date": "Start Time",
                    "duration": "Duration (s)"
                }),
                hide_index=True,
                use_container_width=True
            )
            
            # Visualization of migrations
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Migration Status")
                status_counts = migrations_df['state'].value_counts().reset_index()
                st.bar_chart(status_counts, x='state', y='count')
            
            with col2:
                st.subheader("Migration Durations")
                fig = px.bar(migrations_df, x='version', y='duration', 
                            title="Migration Duration by Version")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No migration history available for this ledger")
    else:
        st.info("No ledgers found in the system")

# 2. Transactions View
elif view == "Transactions":
    st.header("Transactions")
    
    # Filters for transactions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create a dropdown to filter by ledger
        ledgers = list_ledgers()
        if ledgers:
            ledger_names = [l['name'] for l in ledgers]
            default_index = 0  # Pre-select the first ledger
            selected_ledger = st.selectbox("Select a ledger:", ledger_names, index=default_index, key="transaction_ledger_filter")
            filter_ledger = selected_ledger
            st.session_state['selected_ledger'] = filter_ledger
        else:
            st.warning("No ledgers available.")

            
    with col2:
        source_filter = st.text_input("Source Account", value=st.session_state['source_filter'])
    
    with col3:
        destination_filter = st.text_input("Destination Account", value=st.session_state['destination_filter'])
    
    # Apply filters button
    if st.button("Apply Filters"):
        st.session_state['selected_ledger'] = filter_ledger
        st.session_state['source_filter'] = source_filter
        st.session_state['destination_filter'] = destination_filter
        st.rerun()
    
    
    # Show transaction detail or list
    if st.session_state['view_tx_details'] and st.session_state['selected_ledger'] and st.session_state['selected_tx_id']:
        # Transaction Detail View
        tx = get_transaction(st.session_state['selected_ledger'], st.session_state['selected_tx_id'])
        
        if tx:
            # Breadcrumb navigation
            st.markdown(f"**All ledgers > {st.session_state['selected_ledger']} > Transactions > {st.session_state['selected_tx_id']}**")
            
            # Transaction header
            st.subheader(f"Transaction {str(tx.get('id', '')).zfill(7)}")
            
            # Back button
            if st.button("Back to Transactions"):
                st.session_state['view_tx_details'] = False
                st.rerun()
            
            # Postings
            st.write("### Postings")
            if tx.get('postings'):
                postings_data = []
                tx_id = tx.get('id')
                for posting in tx['postings']:
                    postings_data.append({
                        "Txid": str(tx_id).zfill(7),
                        "Value": f"{posting.get('asset')} {posting.get('amount')}",
                        "Source": posting.get('source'),
                        "Destination": posting.get('destination'),
                        "Ledger": st.session_state['selected_ledger'],
                        "Date": tx.get('timestamp')
                    })
                
                st.dataframe(pd.DataFrame(postings_data), hide_index=True, use_container_width=True)
            
            # Graph
            st.write("### Graph")
            graph_data = generate_transaction_graph(tx)
            st.image(f"data:image/png;base64,{graph_data}")
            
            # Metadata
            st.write("### Metadata")
            st.json(tx.get('metadata', {}))
    else:
        # Transaction List View
        transactions = get_transactions(
            st.session_state['selected_ledger'],
            st.session_state['source_filter'],
            st.session_state['destination_filter']
        )
        
        if transactions:
            tx_data = []
            for tx in transactions:
                for posting in tx.get('postings', []):
                    tx_data.append({
                        "Txid": str(tx.get('id')).zfill(7),
                        "Value": f"{posting.get('asset')} {posting.get('amount')}",
                        "Source": posting.get('source'),
                        "Destination": posting.get('destination'),
                        "Ledger": tx.get('ledger'),
                        "Date": tx.get('timestamp')
                    })
            
            df = pd.DataFrame(tx_data)
            
            # Display dataframe with selection
            event = st.dataframe(df, hide_index=True, use_container_width=True,on_select='rerun',selection_mode='single-row')

            if event and len(event.selection['rows']):
                selected_row = event.selection['rows'][0]
                tx_id = df.iloc[selected_row]["Txid"]
                ledger = df.iloc[selected_row]["Ledger"]

                # Set selected transaction and show details
                st.session_state['selected_tx_id'] = tx_id.lstrip('0')
                st.session_state['selected_ledger'] = ledger
                st.session_state['view_tx_details'] = True
                st.rerun()
        else:
            st.info("No transactions found with the selected filters")

# 3. Accounts View
elif view == "Accounts":
    st.header("Accounts")
    
    # Filter by ledger
    ledgers = list_ledgers()
    if ledgers:
        ledger_names = [l['name'] for l in ledgers]
        default_index = 0  # Pre-select the first ledger
        selected_ledger = st.selectbox("Select a ledger:", ledger_names, index=default_index, key="temp_filter", on_change=update_filter)
        st.session_state['selected_ledger'] = selected_ledger
    else:
        st.warning("No ledgers available.")


    if st.session_state['view_account_details'] and st.session_state['selected_account']:
        # Account Detail View
        if st.session_state['selected_ledger']: #Check if there is selected ledger
            account = get_account(st.session_state['selected_ledger'], st.session_state['selected_account'])
            if account:
                # Breadcrumb navigation
                st.markdown(f"**All ledgers > {st.session_state['selected_ledger']} > Accounts > {st.session_state['selected_account']}**")

                # Account header
                st.subheader(f"{account.get('address', '')}")

                # Back button
                if st.button("Back to Accounts"):
                    st.session_state['view_account_details'] = False
                    st.rerun()

                # Activity visualization
                st.write("### Transactions volume")

                # Helper function to process transaction data
                def get_transaction_volume_data(ledger, account):
                    txs = get_transactions(ledger, source=account)
                    volume_data = []

                    for tx in txs:
                        # Check if account is involved in any postings
                        involved = any(
                            posting['source'] == account or posting['destination'] == account
                            for posting in tx.get('postings', [])
                        )
                        
                        if involved:
                            date = pd.to_datetime(tx['timestamp']).strftime('%b %d, %Y')
                            for posting in tx['postings']:
                                if posting['source'] == account or posting['destination'] == account:
                                    volume_data.append({
                                        'date': date,
                                        'asset': posting['asset'],
                                        'amount': abs(float(posting['amount']))
                                    })

                    return pd.DataFrame(volume_data)

                # Get and plot data
                if st.session_state['selected_ledger'] and st.session_state['selected_account']:
                    activity_df = get_transaction_volume_data(
                        st.session_state['selected_ledger'],
                        st.session_state['selected_account']
                    )
                    
                    if not activity_df.empty:
                        # Group by date and asset
                        grouped_df = activity_df.groupby(['date', 'asset'])['amount'].sum().reset_index()
                        
                        # Create stacked bar chart
                        fig = px.bar(
                            grouped_df,
                            x='date',
                            y='amount',
                            color='asset',
                            title=f"Transaction Volume for {st.session_state['selected_account']}",
                            labels={'date': 'Date', 'amount': 'Volume', 'asset': 'Asset'},
                            barmode='stack'
                        )
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Total Volume",
                            hovermode='x unified',
                            xaxis=dict(
                                tickangle=45,
                                tickformat='%b %d, %Y'
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No transaction volume data available")
            else:
                st.warning("Select an account to view transaction volume")

            # Balances and Volumes
            col1, col2 = st.columns(2)

            with col1:
                st.write("### Balances")
                balances = []
                for asset, balance in account.get('balances', {}).items():
                    balances.append({"Asset": asset, "Balance": balance})

                st.dataframe(pd.DataFrame(balances) if balances else pd.DataFrame({"Asset": [], "Balance": []}),
                             hide_index=True, use_container_width=True)

            with col2:
                st.write("### Volumes")
                volumes = []
                volumes_data = account.get('volumes', {})

                for asset, volume in volumes_data.items():
                    volumes.append({
                        "Asset": asset,
                        "Received": volume.get('input', 0),
                        "Sent": volume.get('output', 0)
                    })

                st.dataframe(pd.DataFrame(volumes) if volumes else pd.DataFrame({"Asset": [], "Received": [], "Sent": []}),
                             hide_index=True, use_container_width=True)

            # Transactions for this account
            st.write("### Transactions")
            acc_txs = get_transactions(
                st.session_state['selected_ledger'],
                source=st.session_state['selected_account']
            )

            if acc_txs:
                tx_data = []
                for tx in acc_txs:
                    for posting in tx.get('postings', []):
                        if posting.get('source') == st.session_state['selected_account'] or posting.get('destination') == st.session_state['selected_account']:
                            tx_data.append({
                                "Txid": str(tx.get('id')).zfill(7),
                                "Value": f"{posting.get('asset')} {posting.get('amount')}",
                                "Source": posting.get('source'),
                                "Destination": posting.get('destination'),
                                "Ledger": tx.get('ledger'),
                                "Date": tx.get('timestamp')
                            })

                df = pd.DataFrame(tx_data)

                # Display transactions table
                # event = st.dataframe(df, hide_index=True, use_container_width=True,on_select='rerun',selection_mode='single-row')
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("No transactions found for this account")

            # Metadata
            st.write("### Metadata")
            st.json(account.get('metadata', {}))
    else:
        # Account List View
        accounts = get_accounts(st.session_state['selected_ledger'])

        if accounts:
            account_data = []
            for acc in accounts:
                account_data.append({
                    "Address": acc.get('address'),
                    "Ledger": acc.get('ledger'),
                    "Metadata": str(acc.get('metadata', {}))
                })

            df = pd.DataFrame(account_data)

            # Display accounts table
            event = st.dataframe(df, hide_index=True, use_container_width=True,on_select='rerun',selection_mode='single-row')

            if event and len(event.selection['rows']):
                selected_row = event.selection['rows'][0]
                address = df.iloc[selected_row]["Address"]
                ledger = df.iloc[selected_row]["Ledger"]

                # Set selected account using the ledger from the account's data
                st.session_state['selected_account'] = address
                st.session_state['selected_ledger'] = ledger
                st.session_state['view_account_details'] = True
                st.rerun()
        else:
            st.info("No accounts found with the selected filter")

elif view == "Assets":
    st.header("Asset Management")
    
    # List all unique assets across all ledgers
    all_assets = set()
    for ledger in list_ledgers():
        accounts = get_accounts(ledger['name'])
        for account in accounts:
            if account is not None:
                acc = get_account(ledger['name'], account['address'])
                if acc is not None:
                    all_assets.update(acc.get('balances', {}).keys())
    
    # Display asset list
    st.subheader("All Assets")
    asset_df = pd.DataFrame({"Asset": list(all_assets)})
    st.dataframe(asset_df, hide_index=True, use_container_width=True)
    
    # Asset details section
    st.subheader("Asset Details")
    selected_asset = st.selectbox("Select an asset", list(all_assets), key="asset_selector")
    
    if selected_asset:
        # Calculate total supply
        total_supply = 0
        holding_accounts = []
        for ledger in list_ledgers():
            accounts = get_accounts(ledger['name'])
            for account in accounts:
                acc_details = get_account(ledger['name'], account['address'])
                if acc_details:
                    balance = acc_details.get('balances', {}).get(selected_asset, 0)
                    print(balance)
                    total_supply += float(balance)
                    if balance != 0:  # Include all non-zero balances
                        holding_accounts.append({
                            "Account": account['address'],
                            "Ledger": ledger['name'],
                            "Balance": balance
                        })
        
        st.metric("Total Supply", f"{total_supply:,}")
        
        # Show accounts holding this asset
        st.write("### Accounts Holding This Asset")
        if holding_accounts:
            df = pd.DataFrame(holding_accounts)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("No accounts currently hold this asset.")

# Transaction form in sidebar
SHOW_TRANSACTION_FORM = os.environ.get('SHOW_TRANSACTION_FORM', 'false').lower() == 'true'
with st.sidebar:
    st.markdown("---")
    if SHOW_TRANSACTION_FORM:
        with st.form("transaction_form"):
            st.subheader("Create Transaction")
            form_ledger = st.selectbox("Ledger", [l['name'] for l in list_ledgers()], key="transaction_form_ledger")
            src = st.text_input("Source Account")
            dst = st.text_input("Destination Account")
            amount = st.number_input("Amount", min_value=0.01)
            
            # Add PHP to the list of common assets
            common_assets = ["USD/2", "EUR/2", "JPY/0", "GBP/2", "PHP/2", "BTC/8", "ETH/18"]
            asset_choice = st.selectbox("Asset", options=common_assets + ["Custom"], key="transaction_form_asset")
            
            if asset_choice == "Custom":
                asset = st.text_input("Custom Asset (e.g., GOLD/3)")
            else:
                asset = asset_choice
            
            if st.form_submit_button("Submit"):
                payload = {
                    "postings": [{
                        "source": src,
                        "destination": dst,
                        "amount": int(amount * 100),
                        "asset": asset
                    }],
                    "metadata": {
                        "created_via": "Streamlit UI"
                    }
                }
                
                try:
                    response = requests.post(
                        f"{BASE_URL}/{form_ledger}/transactions",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        st.success("Transaction created successfully!")
                    else:
                        error = response.json()
                        st.error(f"Error: {error.get('errorMessage', 'Unknown error')}")
                except Exception as e:
                    st.error(f"API Error: {str(e)}")
    else:
        st.info("Transaction creation via UI is disabled in this environment.")
        
st.sidebar.markdown("---")
st.sidebar.info("Formance Ledger Dashboard v2.0")
