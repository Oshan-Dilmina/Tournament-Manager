# Tournament Manager 

A tournament management engine built with **Python** and **Flask**. Currently only supported for **Scrabble**,

> [!IMPORTANT]  
> **Note:** This project is in active development. Features like UI enhancements, advanced tie-breaking, and pairing exports are currently under construction.


## ⚙️ Installation & Setup

### 1. Clone & Install
```bash
git clone https://github.com/Oshan-Dilmina/Tournament-Manager
cd Tournament-Manager
pip install -r requirements.txt
```
### 2. Google Firestore Setup
You need a service account key to allow the app to talk to your database:

1. **Go to the** [Google Cloud Console](https://console.cloud.google.com).

2. **Enable Firestore**: Select "Native Mode" and create a database.

3. **Create Service Account**: Navigate to IAM & Admin > Service Accounts.

4. **Generate Key**: Under the Keys tab for that account, click ``Add Key`` > ``Create new key (JSON)``.

5. **Save**: Download the file to your project root as `service-account.json`

> [!IMPORTANT]  
> **Note:** You should save the JSON file including the key as exactly as above.

### 3. Environment Variables

Create a `.env` file in your root directory

``` env
FLASK_SECRET_KEY =Use_a_random_string_here
GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
```
> [!IMPORTANT]  
> **Note:** You should name the variables exactly as showen above.

### 4. Start the Programme

``` bash
py app.py
```
Then open [locahost:5000](http://127.0.0.1:5000) from your browser

> [!IMPORTANT]  
> **Note:** Make sure you have no other programmes using the port `5000`, or change the port in the `app.py` file.

## 📈 Roadmap & Limitations

* **Pairing Systems**: Currently only supports the Swiss System.
* **Games**: Currently the software can be only used for *scrabble*;support for *chess* is planned
* **Tie-breaking**: Standings are currently calculated solely by margins.
* **UI/UX**: A full interface overhaul is in progress.
* **Exports**: "Download Pairings" (PDF/CSV) functionality is coming soon.
* **We are working toward a fully hosted web version of Tournament Manager,So users can host tournaments directly in their browser without needing to clone the repository or set up a local environment.**





